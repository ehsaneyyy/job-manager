import { useEffect, useRef, useState } from "react";
import { Bot, Send, Wrench, AlertCircle } from "lucide-react";
import { cn } from "../../lib/utils";

interface ChatMessage {
  id: number;
  role: string;
  content: string;
  toolUsed: string;
  createdAt: string;
}

export default function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { fetchChatHistory } = await import("../../lib/api");
        const history = await fetchChatHistory();
        if (!cancelled) setMessages(history);
      } catch {
        if (!cancelled) setError("Could not load history. Check server and API key in Settings.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isSending]);

  async function handleSend() {
    const text = input.trim();
    if (!text || isSending) return;
    setInput("");
    setError("");

    const optimisticUser: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: text,
      toolUsed: "",
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUser]);
    setIsSending(true);

    try {
      const { sendChatMessage } = await import("../../lib/api");
      const result = await sendChatMessage(text);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: result.reply,
          toolUsed: result.toolsUsed.join(", "),
          createdAt: new Date().toISOString(),
        },
      ]);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Failed to send. Check server and API key.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <Bot size={40} className="text-accent" />
            <p className="max-w-xs text-sm text-text-muted">
              Try: "Check my inbox", "Apply to this job: [url]", "What's my application stat?"
            </p>
          </div>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed",
              message.role === "user"
                ? "self-end bg-accent-soft text-text-primary"
                : "self-start bg-surface border border-surface-light/50"
            )}
          >
            {message.role === "assistant" && message.toolUsed && (
              <div className="mb-1.5 flex items-center gap-1.5 text-[11px] text-text-muted">
                <Wrench size={12} />
                {message.toolUsed.length > 120 ? `${message.toolUsed.slice(0, 120)}…` : message.toolUsed}
              </div>
            )}
            {message.content}
          </div>
        ))}
        {isSending && (
          <div className="flex items-center gap-2 self-start text-sm text-text-muted">
            <span className="inline-block size-2 animate-pulse rounded-full bg-accent" />
            JobBot is thinking…
          </div>
        )}
      </div>

      {error && (
        <div className="mx-4 mb-2 flex items-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      <div className="border-t border-surface-light/50 p-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSend();
              }
            }}
            rows={1}
            placeholder="Tell JobBot what to do…"
            className="max-h-32 flex-1 resize-none rounded-2xl border border-surface-light bg-surface px-4 py-2.5 text-sm outline-none focus:border-accent"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isSending}
            className="rounded-2xl bg-accent-soft p-3 text-accent transition-colors hover:bg-accent hover:text-background disabled:opacity-40"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}