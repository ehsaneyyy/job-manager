import base64
import ctypes
import hashlib
import json
import os
import secrets
from ctypes import wintypes
from pathlib import Path

from fastapi import Header, HTTPException, status

from app.core.config import settings


def generate_random_secret(length: int = 48) -> str:
    return secrets.token_urlsafe(length)


def require_valid_api_key(x_api_key: str = Header(default="")) -> None:
    if not settings.api_key or len(settings.api_key) < 16:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server API key is not configured. Set API_KEY in backend\\.env.",
        )
    expected_hash = hmac_digest(settings.api_key)
    provided_hash = hmac_digest(x_api_key)
    if not secrets.compare_digest(expected_hash, provided_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Add header X-API-Key with the key from backend\\.env.",
        )


def hmac_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _protect_with_dpapi(plaintext_bytes: bytes) -> bytes:
    input_blob = _DataBlob(
        len(plaintext_bytes),
        ctypes.cast(ctypes.create_string_buffer(plaintext_bytes), ctypes.POINTER(ctypes.c_char)),
    )
    output_blob = _DataBlob()
    success = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(input_blob), None, None, None, None, 0, ctypes.byref(output_blob)
    )
    if not success:
        raise OSError("Windows DPAPI protection failed")
    return ctypes.string_at(output_blob.pbData, output_blob.cbData)


def _unprotect_with_dpapi(protected_bytes: bytes) -> bytes:
    input_blob = _DataBlob(
        len(protected_bytes),
        ctypes.cast(ctypes.create_string_buffer(protected_bytes), ctypes.POINTER(ctypes.c_char)),
    )
    output_blob = _DataBlob()
    success = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(input_blob), None, None, None, None, 0, ctypes.byref(output_blob)
    )
    if not success:
        raise OSError("Windows DPAPI unprotection failed")
    return ctypes.string_at(output_blob.pbData, output_blob.cbData)


class CredentialVault:
    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path
        self._contents: dict[str, dict[str, str]] = {}
        if self.vault_path.exists():
            try:
                raw = json.loads(self.vault_path.read_text(encoding="utf-8"))
                for key, wrapped in raw.items():
                    self._contents[key] = self._unwrap(wrapped)
            except Exception:
                self._contents = {}

    def _wrap(self, plaintext_value: str) -> dict[str, str]:
        if os.name == "nt":
            return {"cipher": "dpapi", "payload": base64.b64encode(_protect_with_dpapi(plaintext_value.encode("utf-8"))).decode("ascii")}
        return {"cipher": "obfuscated", "payload": base64.b64encode(plaintext_value.encode("utf-8")).decode("ascii")}

    def _unwrap(self, wrapped: dict[str, str]) -> str:
        payload = base64.b64decode(wrapped["payload"])
        if wrapped.get("cipher") == "dpapi":
            return _unprotect_with_dpapi(payload).decode("utf-8")
        return payload.decode("utf-8")

    def _persist(self) -> None:
        serializable: dict[str, dict[str, str]] = {}
        for key, value in self._contents.items():
            serializable[key] = self._wrap(value)
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        self.vault_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")

    def store(self, key: str, value: str) -> None:
        self._contents[key] = value
        self._persist()

    def retrieve(self, key: str) -> str | None:
        return self._contents.get(key)

    def remove(self, key: str) -> None:
        self._contents.pop(key, None)
        self._persist()

    def keys(self) -> list[str]:
        return list(self._contents.keys())


vault = CredentialVault(settings.data_dir / "vault")