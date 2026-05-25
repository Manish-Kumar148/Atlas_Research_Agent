"use client";
import { useEffect, useRef } from "react";
import { useResearchStore } from "@/store/researchStore";
import { AgentEvent } from "@/types";
import { AGENT_DEFINITIONS } from "@/types";

const AGENT_MAP = Object.fromEntries(AGENT_DEFINITIONS.map((a) => [a.id, a]));

function ToolBadge({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px]
      font-mono bg-accent/10 text-accent border border-accent/20 mr-1 mt-1">
      ⚡ {name}
    </span>
  );
}

function FeedCard({ event }: { event: AgentEvent }) {
  const agent = AGENT_MAP[event.agent_id];
  const displayAgent = agent || {
    name: "Pipeline",
    icon: "!",
    color: "#ef4444",
  };

  const data = event.data as Record<string, unknown>;

  return (
    <div className="flex gap-3 mb-4 animate-fade-in">
      {/* Timeline */}
      <div className="flex flex-col items-center">
        <div className="w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0"
          style={{ background: displayAgent.color }} />
        <div className="w-px bg-border flex-1 mt-1" />
      </div>

      {/* Body */}
      <div className="flex-1 pb-1">
        <div className="text-[10px] font-semibold tracking-wider uppercase mb-1"
          style={{ color: displayAgent.color }}>
          {displayAgent.icon} {displayAgent.name}
        </div>

        <div className="bg-bg1 border border-border rounded-xl px-3.5 py-3 text-[12px]">
          <div className="font-semibold text-text mb-1.5">
            {event.event === "error" ? "⚠️ Error" : "✦ " + eventTitle(event)}
          </div>
          <div className="text-text2 leading-relaxed">{event.summary}</div>

          {/* Tool calls */}
          {event.tool_calls?.length > 0 && (
            <div className="mt-2">
              {event.tool_calls.map((t, i) => <ToolBadge key={i} name={t} />)}
            </div>
          )}

          {/* Structured data previews */}
          {event.agent_id === "planning" && data.search_queries && (
            <div className="mt-2.5 space-y-1">
              {(data.search_queries as string[]).slice(0, 4).map((q, i) => (
                <div key={i} className="text-[10px] font-mono text-text3 truncate">
                  → {q}
                </div>
              ))}
            </div>
          )}

          {event.agent_id === "knowledge_extraction" && data.type_breakdown && (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {Object.entries(data.type_breakdown as Record<string,number>).map(([t, n]) => (
                <span key={t} className="text-[10px] px-2 py-0.5 rounded bg-bg2 border border-border text-text2">
                  {t}: {n}
                </span>
              ))}
            </div>
          )}

          {event.agent_id === "reflection" && data.score !== undefined && (
            <div className={`mt-2.5 p-2.5 rounded-lg border text-[11px]
              ${Number(data.score) >= 0.85
                ? "bg-accent3/5 border-accent3/20 text-accent3"
                : "bg-accent4/5 border-accent4/20 text-accent4"}`}>
              <div className="font-semibold text-[10px] uppercase tracking-wider opacity-70 mb-1">
                🪞 Reflection
              </div>
              {String(Math.round(Number(data.score) * 100))}% complete
              {data.gaps && (data.gaps as string[]).length > 0 && (
                <div className="mt-1 opacity-80">
                  Gaps: {(data.gaps as string[]).join("; ")}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function eventTitle(event: AgentEvent): string {
  const titles: Record<string, string> = {
    task_understanding: "Research Intent Parsed",
    planning:           "Roadmap Generated",
    web_research:       "Web Search Complete",
    knowledge_extraction: "Insights Extracted",
    memory_agent:       "Memory Persisted",
    reflection:         "Quality Evaluated",
    report_generation:  "Report Generated",
  };
  return titles[event.agent_id] || event.event;
}

export default function LiveFeed() {
  const { feedEvents, status } = useResearchStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [feedEvents.length]);

  if (feedEvents.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-10">
        <div className="text-5xl opacity-40">🔬</div>
        <div className="text-[14px] font-medium text-text2">Atlas is ready</div>
        <div className="text-[12px] text-text3 max-w-[260px] leading-relaxed">
          Enter a research objective and launch the autonomous agent pipeline to begin.
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-5">
      {feedEvents.map((event, i) => (
        <FeedCard key={i} event={event} />
      ))}

      {/* Typing indicator when running */}
      {status === "running" && (
        <div className="flex gap-3 mb-4">
          <div className="flex flex-col items-center">
            <div className="w-2.5 h-2.5 rounded-full bg-accent/50 mt-1" />
          </div>
          <div className="bg-bg1 border border-border rounded-xl px-3.5 py-3">
            <div className="flex gap-1.5">
              {[0, 1, 2].map((i) => (
                <div key={i} className="w-1.5 h-1.5 rounded-full bg-text3"
                  style={{ animation: `typing 1.2s ${i * 0.2}s infinite` }} />
              ))}
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
