import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, Plus, RefreshCcw, Trash2 } from "lucide-react";
import { createJob, deleteJob, fetchJobs, updateJob } from "../../lib/api";
import type { Job } from "../../lib/api";
import Card from "../../components/ui/card";
import FormInput from "../../components/ui/input";
import { cn, formatDateTime } from "../../lib/utils";

const statusOptions = ["applied", "under_review", "interview", "declined", "accepted", "no_response"];
const statusTone: Record<string, string> = {
  applied: "text-warning",
  under_review: "text-accent",
  interview: "text-success",
  declined: "text-danger",
  accepted: "text-success",
  no_response: "text-text-muted",
};

function AddJobForm({ onAdded }: { onAdded: () => void }) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: createJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      onAdded();
    },
  });
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [platform, setPlatform] = useState("other");
  const [url, setUrl] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!company.trim() || !role.trim()) return;
    mutation.mutate({
      company: company.trim(),
      role: role.trim(),
      platform,
      jobUrl: url.trim(),
    });
    setCompany("");
    setRole("");
    setUrl("");
  }

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-2">
      <FormInput
        placeholder="Company"
        value={company}
        onChange={(e) => setCompany(e.target.value)}
      />
      <FormInput
        placeholder="Role"
        value={role}
        onChange={(e) => setRole(e.target.value)}
      />
      <FormInput
        placeholder="Job URL (optional)"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="col-span-2"
      />
      <select
        value={platform}
        onChange={(e) => setPlatform(e.target.value)}
        className="rounded-2xl border border-surface-light bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
      >
        <option value="other">Other</option>
        <option value="linkedin">LinkedIn</option>
        <option value="indeed">Indeed</option>
        <option value="email">Email</option>
      </select>
      <button
        type="submit"
        disabled={!company.trim() || !role.trim() || mutation.isPending}
        className="rounded-2xl bg-accent-soft px-4 py-2 text-sm font-medium text-accent transition-colors hover:bg-accent hover:text-background disabled:opacity-40"
      >
        {mutation.isPending ? "Adding…" : "Add job"}
      </button>
      {mutation.isError && (
        <p className="col-span-2 text-xs text-danger">
          {mutation.error instanceof Error ? mutation.error.message : "Failed to add job"}
        </p>
      )}
    </form>
  );
}

function JobRow({ job }: { job: Job }) {
  const queryClient = useQueryClient();
  const updateMutation = useMutation({
    mutationFn: (newStatus: string) => updateJob(job.id, { status: newStatus }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });
  const deleteMutation = useMutation({
    mutationFn: () => deleteJob(job.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-semibold">{job.role}</h3>
            <span className="rounded-full bg-surface-light/40 px-2 py-0.5 text-[10px] uppercase tracking-wide text-text-muted">
              {job.platform}
            </span>
          </div>
          <p className="mt-0.5 text-sm text-text-muted">{job.company}</p>
        </div>
        <button
          onClick={() => {
            if (confirm("Delete this job?")) deleteMutation.mutate();
          }}
          className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-danger/10 hover:text-danger"
        >
          <Trash2 size={16} />
        </button>
      </div>

      {job.jobUrl && (
        <a
          href={job.jobUrl}
          target="_blank"
          rel="noreferrer"
          className="mt-2 block truncate text-xs text-accent underline-offset-2 hover:underline"
        >
          {job.jobUrl}
        </a>
      )}

      <div className="mt-3 flex items-center justify-between gap-2">
        <select
          value={job.status}
          onChange={(e) => updateMutation.mutate(e.target.value)}
          className={cn(
            "rounded-xl border border-surface-light bg-surface px-2.5 py-1.5 text-xs font-medium outline-none focus:border-accent",
            statusTone[job.status] ?? "text-text-muted"
          )}
        >
          {statusOptions.map((option) => (
            <option key={option} value={option} className="text-text-primary">
              {option.replace("_", " ")}
            </option>
          ))}
        </select>
        <span className="text-[10px] text-text-muted">
          {formatDateTime(job.appliedAt)}
          {job.nextFollowUp ? ` · follow up: ${formatDateTime(job.nextFollowUp)}` : ""}
        </span>
      </div>

      {job.notes && <p className="mt-2 text-xs text-text-muted">{job.notes}</p>}
    </Card>
  );
}

export default function JobsView() {
  const [showAddForm, setShowAddForm] = useState(false);
  const { data: jobs = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => fetchJobs(),
  });

  return (
    <div className="space-y-3 overflow-y-auto p-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Applications ({jobs.length})</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="rounded-xl bg-surface p-2 text-text-muted transition-colors hover:text-accent"
          >
            <RefreshCcw size={16} />
          </button>
          <button
            onClick={() => setShowAddForm((show) => !show)}
            className="flex items-center gap-1 rounded-xl bg-accent-soft px-3 py-2 text-sm font-medium text-accent transition-colors hover:bg-accent hover:text-background"
          >
            <Plus size={16} />
            Add job
          </button>
        </div>
      </div>

      {showAddForm && (
        <AddJobForm
          onAdded={() => setShowAddForm(false)}
        />
      )}

      {isLoading && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-2xl bg-surface" />
          ))}
        </div>
      )}
      {isError && (
        <p className="text-sm text-danger">Could not load jobs. Check server + API key in Settings.</p>
      )}
      {!isLoading && jobs.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-10 text-center">
          <Briefcase size={36} className="text-text-muted" />
          <p className="text-sm text-text-muted">No jobs tracked yet. Add one or ask JobBot to track applications.</p>
        </div>
      )}
      {jobs.map((job) => (
        <JobRow key={job.id} job={job} />
      ))}
    </div>
  );
}