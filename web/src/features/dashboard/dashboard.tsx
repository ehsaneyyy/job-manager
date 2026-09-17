import { useQuery } from "@tanstack/react-query";
import { Briefcase, CheckCircle2, FileQuestion, MessageSquare, TrendingUp, Inbox, Reply, FileText } from "lucide-react";
import { fetchDashboardStats } from "../../lib/api";
import Card from "../../components/ui/card";

const statusConfig = [
  { key: "awaitingReply", label: "Awaiting reply", color: "text-warning", icon: FileQuestion },
  { key: "underReview", label: "Under review", color: "text-accent", icon: FileText },
  { key: "interview", label: "Interview", color: "text-success", icon: MessageSquare },
  { key: "declined", label: "Declined", color: "text-danger", icon: Briefcase },
  { key: "accepted", label: "Accepted", color: "text-success", icon: CheckCircle2 },
  { key: "noResponse", label: "No response", color: "text-text-muted", icon: Briefcase },
] as const;

export default function DashboardView() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboardStats,
  });

  if (isLoading) {
    return (
      <div className="grid gap-3 p-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded-2xl bg-surface" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-4 text-sm text-danger">
        Could not load stats. Check server + API key in Settings.{" "}
        {error instanceof Error ? error.message : ""}
      </div>
    );
  }

  const knownStatuses = statusConfig;
  const unknownCount =
    data.totalApplied -
    statusConfig.reduce((sum, item) => sum + data[item.key], 0);

  return (
    <div className="space-y-4 overflow-y-auto p-4">
      <div className="grid grid-cols-2 gap-3">
        <Card>
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-muted">Total applied</span>
            <TrendingUp size={16} className="text-accent" />
          </div>
          <p className="mt-2 text-3xl font-bold">{data.totalApplied}</p>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-muted">Reply rate</span>
            <MessageSquare size={16} className="text-success" />
          </div>
          <p className="mt-2 text-3xl font-bold">{data.replyRate}%</p>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Card>
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Inbox size={16} className="text-accent" />
            Emails seen
          </div>
          <p className="mt-2 text-2xl font-bold">{data.emailsSeen}</p>
        </Card>
        <Card>
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Reply size={16} className="text-success" />
            Emails replied
          </div>
          <p className="mt-2 text-2xl font-bold">{data.emailsReplied}</p>
        </Card>
      </div>

      <div className="space-y-2">
        <h2 className="text-sm font-semibold text-text-muted">Application statuses</h2>
        {knownStatuses.map((item) => {
          const Icon = item.icon;
          const count = data[item.key];
          return (
            <div key={item.key} className="flex items-center gap-3 rounded-xl bg-surface px-4 py-2.5">
              <Icon size={16} className={item.color} />
              <span className="flex-1 text-sm">{item.label}</span>
              <span className={`text-sm font-semibold ${item.color}`}>{count}</span>
            </div>
          );
        })}
        {unknownCount > 0 && (
          <div className="flex items-center gap-3 rounded-xl bg-surface px-4 py-2.5">
            <Briefcase size={16} className="text-text-muted" />
            <span className="flex-1 text-sm">Other</span>
            <span className="text-sm font-semibold text-text-muted">{unknownCount}</span>
          </div>
        )}
        {data.emailsUnread > 0 && (
          <p className="pt-2 text-xs text-warning">
            {data.emailsUnread} unread email{data.emailsUnread === 1 ? "" : "s"} — try asking JobBot to check your inbox.
          </p>
        )}
      </div>
    </div>
  );
}