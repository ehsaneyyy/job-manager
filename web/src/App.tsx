import { useState } from "react";
import { Bot, Inbox, LayoutDashboard, Briefcase, Settings } from "lucide-react";
import { cn } from "./lib/utils";
import ChatView from "./features/chat/chat";
import DashboardView from "./features/dashboard/dashboard";
import JobsView from "./features/jobs/jobs";
import EmailsView from "./features/emails/emails";
import SettingsView from "./features/settings/settings";

type ViewKey = "chat" | "dashboard" | "jobs" | "emails" | "settings";

const tabOrder: { key: ViewKey; label: string; icon: React.ElementType }[] = [
  { key: "chat", label: "Chat", icon: Bot },
  { key: "dashboard", label: "Stats", icon: LayoutDashboard },
  { key: "jobs", label: "Jobs", icon: Briefcase },
  { key: "emails", label: "Emails", icon: Inbox },
  { key: "settings", label: "Settings", icon: Settings },
];

export default function App() {
  const [activeView, setActiveView] = useState<ViewKey>("chat");

  return (
    <div className="flex h-full flex-col bg-background text-text-primary">
      <header className="flex items-center justify-between border-b border-surface-light/50 px-4 py-3">
        <div className="flex items-center gap-2">
          <Bot className="text-accent" />
          <h1 className="text-lg font-semibold tracking-tight">JobBot</h1>
        </div>
        <span className="text-xs text-text-muted">Jobs · Email · Stats</span>
      </header>

      <main className="flex-1 overflow-hidden">
        {activeView === "chat" && <ChatView />}
        {activeView === "dashboard" && <DashboardView />}
        {activeView === "jobs" && <JobsView />}
        {activeView === "emails" && <EmailsView />}
        {activeView === "settings" && <SettingsView />}
      </main>

      <nav className="grid grid-cols-5 border-t border-surface-light/50 bg-surface">
        {tabOrder.map((tab) => {
          const Icon = tab.icon;
          const active = activeView === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveView(tab.key)}
              className={cn(
                "flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium transition-colors",
                active ? "text-accent" : "text-text-muted hover:text-text-primary"
              )}
            >
              <Icon size={20} />
              {tab.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}