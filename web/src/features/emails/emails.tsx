import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Inbox, MailOpen, RefreshCcw } from "lucide-react";
import { fetchEmails, syncInbox } from "../../lib/api";
import type { EmailRecord } from "../../lib/api";
import Card from "../../components/ui/card";
import { cn, formatDateTime } from "../../lib/utils";

function EmailRow({ email }: { email: EmailRecord }) {
  return (
    <Card className={cn("cursor-pointer transition-colors hover:border-surface-light", email.isRead && "opacity-70")}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{email.subject || "(no subject)"}</p>
        </div>
        <span className="shrink-0 text-[10px] text-text-muted">{formatDateTime(email.receivedAt)}</span>
      </div>
      <p className="mt-1 truncate text-xs text-text-muted">{email.sender}</p>
      {email.summary ? (
        <p className="mt-2 text-xs text-text-primary">{email.summary}</p>
      ) : (
        <p className="mt-2 line-clamp-2 text-xs text-text-muted">{email.snippet}</p>
      )}
      <div className="mt-2 flex gap-1.5">
        {!email.isRead && (
          <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-medium text-accent">Unread</span>
        )}
        {email.isReplied && (
          <span className="rounded-full bg-success/10 px-2 py-0.5 text-[10px] font-medium text-success">Replied</span>
        )}
      </div>
    </Card>
  );
}

export default function EmailsView() {
  const queryClient = useQueryClient();
  const [syncError, setSyncError] = useState("");
  const { data: emails = [], isLoading, isError } = useQuery({
    queryKey: ["emails"],
    queryFn: () => fetchEmails(),
  });

  const syncMutation = useMutation({
    mutationFn: () => syncInbox(),
    onSuccess: (result) => {
      setSyncError(result.error || "");
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
    onError: (error) => {
      setSyncError(error instanceof Error ? error.message : "Sync failed");
    },
  });

  return (
    <div className="space-y-3 overflow-y-auto p-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Inbox ({emails.length})</h2>
        <button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="flex items-center gap-1 rounded-xl bg-accent-soft px-3 py-2 text-sm font-medium text-accent transition-colors hover:bg-accent hover:text-background disabled:opacity-40"
        >
          <RefreshCcw size={16} className={syncMutation.isPending ? "animate-spin" : ""} />
          {syncMutation.isPending ? "Syncing…" : "Sync inbox"}
        </button>
      </div>

      {syncError && (
        <p className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">{syncError}</p>
      )}
      {!syncError && emails.length === 0 && !isLoading && (
        <div className="flex flex-col items-center gap-2 py-10 text-center">
          <Inbox size={36} className="text-text-muted" />
          <p className="text-sm text-text-muted">
            No emails loaded. Connect Gmail in Settings, then sync.
          </p>
        </div>
      )}
      {isLoading && [0, 1, 2].map((i) => <div key={i} className="h-24 animate-pulse rounded-2xl bg-surface" />)}
      {isError && <p className="text-sm text-danger">Could not load emails. Check server + API key in Settings.</p>}
      {emails.map((email) => (
        <EmailRow key={email.id} email={email} />
      ))}

      <div className="flex items-center gap-2 text-xs text-text-muted">
        <MailOpen size={14} />
        The agent reads the full thread — just ask about a company in Chat.
      </div>
    </div>
  );
}