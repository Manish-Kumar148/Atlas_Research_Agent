"use client";
import { useState } from "react";
import { useResearchStore } from "@/store/researchStore";
import ResearchInput from "@/components/ResearchInput";
import AgentPipeline from "@/components/AgentPipeline";
import LiveFeed from "@/components/LiveFeed";
import MemorySidebar from "@/components/MemorySidebar";
import SourcesPanel from "@/components/SourcesPanel";
import ReportViewer from "@/components/ReportViewer";

type Tab = "feed" | "report";
type RightTab = "memory" | "sources";

export default function Home() {
  const { status, topic } = useResearchStore();
  const [tab, setTab] = useState<Tab>("feed");
  const [rightTab, setRightTab] = useState<RightTab>("memory");

  const isActive = status === "running";
  const isComplete = status === "completed";
  const isFailed = status === "failed";

  return (
    <div className="flex flex-col h-screen bg-bg">
      {/* ── Top bar ─────────────────────────────────────── */}
      <header className="flex items-center gap-3 px-5 h-[52px] bg-bg1 border-b border-border flex-shrink-0 z-10">
        <div className="flex items-center gap-2 text-[15px] font-bold tracking-tight">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center text-[13px] text-white"
            style={{ background: "linear-gradient(135deg,#4f8eff,#7c3aed)" }}>⬡</div>
          Atlas
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full font-medium tracking-wider
          bg-accent/10 text-accent border border-accent/25">
          Research Agent v0.1
        </span>

        <div className="flex-1" />

        {/* Status indicator */}
        <div className="flex items-center gap-2 text-[11px] text-text2">
          <div className={`w-1.5 h-1.5 rounded-full ${
            isActive ? "bg-accent3" : isComplete ? "bg-accent3/50" : isFailed ? "bg-accent4" : "bg-text3"
          }`} style={isActive ? { animation: "pulse-dot 2s infinite" } : {}} />
          {isActive ? "Research running…" : isComplete ? "Research complete" : isFailed ? "Research failed" : "Idle"}
        </div>
      </header>

      {/* ── Main layout ─────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden" style={{ gridTemplateColumns: "300px 1fr 280px" }}>

        {/* Left sidebar */}
        <aside className="w-[300px] flex flex-col bg-bg1 border-r border-border flex-shrink-0 overflow-hidden">
          <ResearchInput />
          <AgentPipeline />
        </aside>

        {/* Center */}
        <main className="flex flex-col flex-1 overflow-hidden">
          {/* Tab header */}
          <div className="flex items-center gap-3 px-5 h-[48px] border-b border-border bg-bg1 flex-shrink-0">
            <div className="flex-1 text-[13px] font-semibold text-text truncate">
              {topic || "No active session"}
            </div>
            <div className="flex gap-0.5 bg-bg2 p-0.5 rounded-lg">
              {(["feed", "report"] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-3 py-1 text-[11px] font-medium rounded-md capitalize transition-all
                    ${tab === t
                      ? "bg-bg1 text-text border border-border2 shadow-sm"
                      : "text-text2 hover:text-text"}`}
                >
                  {t === "feed" ? "Live Feed" : "Report"}
                </button>
              ))}
            </div>
          </div>

          {/* Tab content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {tab === "feed" ? <LiveFeed /> : <ReportViewer />}
          </div>
        </main>

        {/* Right sidebar */}
        <aside className="w-[280px] flex flex-col bg-bg1 border-l border-border flex-shrink-0 overflow-hidden">
          {/* Right tabs */}
          <div className="flex border-b border-border flex-shrink-0">
            {(["memory", "sources"] as RightTab[]).map((t) => (
              <button
                key={t}
                onClick={() => setRightTab(t)}
                className={`flex-1 py-3 text-[11px] font-semibold capitalize tracking-wide transition-colors
                  ${rightTab === t
                    ? "text-text border-b-2 border-accent"
                    : "text-text3 hover:text-text2"}`}
              >
                {t === "memory" ? "🧠 Memory" : "📚 Sources"}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto">
            {rightTab === "memory" ? <MemorySidebar /> : <SourcesPanel />}
          </div>
        </aside>
      </div>
    </div>
  );
}
