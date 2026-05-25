"use client";
import { useState } from "react";
import { useResearchStore } from "@/store/researchStore";
import { MemoryEntry } from "@/types";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function MemorySidebar() {
  const { memories, sessionId, addMemory } = useResearchStore();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MemoryEntry[]>([]);
  const [searching, setSearching] = useState(false);

  async function handleQuery() {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`${BACKEND}/memory/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, session_id: sessionId, top_k: 5 }),
      });
      const data: MemoryEntry[] = await res.json();
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  const displayMemories = results.length > 0 ? results : memories.slice().reverse().slice(0, 8);

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <div className="text-[10px] font-semibold tracking-widest text-text3 uppercase mb-3">
          Memory Context
        </div>
        <div className="flex gap-1.5">
          <input
            className="flex-1 bg-bg2 border border-border2 rounded-lg px-2.5 py-1.5 text-[11px]
              text-text placeholder-text3 outline-none focus:border-accent/50 transition-colors"
            placeholder="Query memory…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleQuery()}
          />
          <button
            onClick={handleQuery}
            disabled={searching}
            className="px-2.5 py-1.5 bg-bg3 border border-border2 rounded-lg text-[11px]
              text-text2 hover:text-text hover:bg-border transition-all disabled:opacity-50"
          >
            {searching ? "…" : "⌕"}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {displayMemories.length === 0 ? (
          <div className="p-4 text-[11px] text-text3">No memory entries yet</div>
        ) : (
          displayMemories.map((m, i) => (
            <div key={i} className="p-3 border-b border-border hover:bg-bg2 cursor-pointer transition-colors">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[11px]">🧠</span>
                <div className="text-[11px] font-medium text-text truncate">
                  {m.content.length > 60 ? m.content.slice(0, 60) + "…" : m.content}
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mt-1">
                {m.tags.slice(0, 3).map((tag) => (
                  <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded bg-accent/10 text-accent">
                    {tag}
                  </span>
                ))}
                {m.similarity_score < 1 && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-bg3 text-text3 font-mono">
                    {Math.round(m.similarity_score * 100)}% sim
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
