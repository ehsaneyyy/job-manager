import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Mail, Plug, Server } from "lucide-react";
import {
  fetchGmailStatus,
  finishGmailConnection,
  getApiBase,
  getApiKey,
  setConnectionSettings,
  startGmailConnection,
} from "../../lib/api";
import Card from "../../components/ui/card";
import FormInput from "../../components/ui/input";

function ConnectionSettings() {
  const [apiKey, setApiKey] = useState(getApiKey());
  const [apiBase, setApiBase] = useState(getApiBase());
  const [saved, setSaved] = useState(false);

  return (
    <Card>
      <div className="flex items-center gap-2">
        <Server size={18} className="text-accent" />
        <h2 className="text-sm font-semibold">Server connection</h2>
      </div>
      <p className="mt-1 text-xs text-text-muted">
        API key comes from <code className="text-accent">backend\.env</code>. On your phone, change the base URL to your PC's address.
      </p>
      <div className="mt-3 space-y-3">
        <div>
          <label className="mb-1 block text-xs text-text-muted">API base URL</label>
          <FormInput value={apiBase} onChange={(e) => setApiBase(e.target.value)} placeholder="http://127.0.0.1:8765" />
        </div>
        <div>
          <label className="mb-1 block text-xs text-text-muted">API key</label>
          <FormInput value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="paste your API key" />
        </div>
        <button
          onClick={() => {
            setConnectionSettings(apiKey.trim(), apiBase.trim());
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
          }}
          className="rounded-2xl bg-accent-soft px-4 py-2.5 text-sm font-medium text-accent transition-colors hover:bg-accent hover:text-background"
        >
          {saved ? "Saved ✓" : "Save connection"}
        </button>
      </div>
    </Card>
  );
}

function GmailConnection() {
  const { data: gmailStatus, refetch } = useQuery({
    queryKey: ["gmail-status"],
    queryFn: fetchGmailStatus,
  });
  const [message, setMessage] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [showManual, setShowManual] = useState(false);

  async function connect() {
    setBusy(true);
    setMessage("");
    try {
      const start = await startGmailConnection();
      if (!start.authorizationUrl || !start.authorizationUrl.startsWith("http")) {
        throw new Error("The server did not return a valid sign-in link. Close run.bat and start it again, then retry.");
      }
      window.location.assign(start.authorizationUrl);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not start Gmail connection");
      setBusy(false);
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-2">
        <Mail size={18} className="text-accent" />
        <h2 className="text-sm font-semibold">Gmail</h2>
        {gmailStatus?.connected ? (
          <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-xs text-success">
            <CheckCircle2 size={12} /> Connected
          </span>
        ) : (
          <span className="rounded-full bg-warning/10 px-2 py-0.5 text-xs text-warning">Not connected</span>
        )}
      </div>

      {!gmailStatus?.connected && (
        <button
          onClick={connect}
          disabled={busy}
          className="mt-3 rounded-2xl bg-accent-soft px-4 py-2.5 text-sm font-medium text-accent transition-colors hover:bg-accent hover:text-background disabled:opacity-40"
        >
          {busy ? "Starting…" : "Connect Gmail"}
        </button>
      )}

      {!gmailStatus?.connected && (
        <button
          onClick={() => setShowManual((shown) => !shown)}
          className="mt-2 flex items-center gap-1 text-xs text-text-muted underline-offset-2 hover:underline"
        >
          Trouble? Paste the code manually
        </button>
      )}

      {showManual && (
        <div className="mt-3 space-y-2">
          <p className="text-xs text-text-muted">
            Use a browser where this app is reachable, click Connect Gmail, sign in, then this page sends you to a JobBot page that says "connected". If you cannot reach that page, copy everything after
            {" "}<code className="text-accent">?</code>{" "}from the Google address bar and paste it here instead.
          </p>
          <div className="flex gap-2">
            <FormInput
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="code=...&state=..."
              className="flex-1"
            />
            <button
              onClick={async () => {
                setBusy(true);
                setMessage("");
                try {
                  await finishGmailConnection(code.trim(), "http://localhost:8766");
                  setMessage("Gmail connected.");
                  setCode("");
                  refetch();
                } catch (error) {
                  setMessage(error instanceof Error ? error.message : "Connection failed");
                } finally {
                  setBusy(false);
                }
              }}
              disabled={!code.trim() || busy}
              className="rounded-2xl bg-accent-soft px-4 py-2 text-sm text-accent hover:bg-accent hover:text-background disabled:opacity-40"
            >
              {busy ? "…" : "Finish"}
            </button>
          </div>
        </div>
      )}

      {message && (
        <p className={`mt-2 text-xs ${/fail|could|did not|cannot|stuck/i.test(message) ? "text-danger" : "text-success"}`}>
          {message}
        </p>
      )}
    </Card>
  );
}

function BrowserLogin() {
  return (
    <Card>
      <div className="flex items-center gap-2">
        <Plug size={18} className="text-accent" />
        <h2 className="text-sm font-semibold">Job platforms (browser)</h2>
      </div>
      <p className="mt-1 text-xs text-text-muted">
        The app opens a browser that needs to be logged into LinkedIn or Indeed once. Log in manually, then click Finish login to save the session.
      </p>
      <div className="mt-3">
        <a href={`${getApiBase()}/docs`} target="_blank" rel="noreferrer" className="text-xs text-accent underline">
          Use the <span className="font-mono">/api/auth/browser/login</span> endpoint in the API docs to start the browser.
        </a>
      </div>
    </Card>
  );
}

export default function SettingsView() {
  return (
    <div className="space-y-4 overflow-y-auto p-4">
      <ConnectionSettings />
      <GmailConnection />
      <BrowserLogin />
    </div>
  );
}