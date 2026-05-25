"use client";
import { useResearchStore } from "@/store/researchStore";
import { AgentStatus } from "@/types";

function StatusBadge({ status, color }: { status: AgentStatus; color: string }) {
  if (status === "active") {
    return (
      <div
        className="w-4 h-4 rounded-full flex items-center justify-center"
        style={{ background: `${color}30` }}
      >
        <div
          className="w-2 h-2 rounded-full"
          style={{ background: color, animation: "pulse-dot 1s infinite" }}
        />
      </div>
    );
  }
  if (status === "done") {
    return (
      <div
        className="w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
        style={{ background: "rgba(16,185,129,.2)", color: "#10b981" }}
      >✓</div>
    );
  }
  if (status === "error") {
    return (
      <div className="w-4 h-4 rounded-full flex items-center justify-center text-[9px]"
        style={{ background: "rgba(239,68,68,.2)", color: "#ef4444" }}>✕</div>
    );
  }
  return (
    <div className="w-4 h-4 rounded-full flex items-center justify-center text-[9px] text-text3 bg-bg3">○</div>
  );
}

export default function AgentPipeline() {
  const { agentStates, progress } = useResearchStore();
  const pct = Math.round((progress / 7) * 100);

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex items-center justify-between px-4 pt-3 pb-1">
        <div className="text-[10px] font-semibold tracking-widest text-text3 uppercase">
          Agent Pipeline
        </div>
        <div className="text-[10px] text-text3 font-mono">{progress} / 7</div>
      </div>

      {/* Progress bar */}
      <div className="mx-4 mb-2 h-[2px] bg-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: "linear-gradient(90deg, #4f8eff, #22d3ee)",
          }}
        />
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-3">
        {agentStates.map((agent) => {
          const isActive = agent.status === "active";
          const isDone   = agent.status === "done";
          const isError  = agent.status === "error";

          return (
            <div
              key={agent.id}
              className={`flex items-center gap-2.5 p-2.5 rounded-lg border mb-1.5 transition-all duration-200
                ${isActive ? "border-accent/30 bg-accent/5"
                  : isDone  ? "border-accent3/20 bg-accent3/4"
                  : isError ? "border-accent5/20 bg-accent5/4"
                  : "border-transparent hover:bg-bg2 hover:border-border"}`}
            >
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center text-base flex-shrink-0"
                style={{ background: `${agent.color}20` }}
              >
                {agent.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[12px] font-semibold text-text truncate">{agent.name}</div>
                <div
                  className="text-[10px] mt-0.5 truncate"
                  style={{ color: isActive ? agent.color : isDone ? "#10b981" : "var(--text3)" }}
                >
                  {agent.statusText}
                </div>
              </div>
              <StatusBadge status={agent.status} color={agent.color} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
