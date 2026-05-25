"use client";
import { useResearchStore } from "@/store/researchStore";

function scoreColor(score: number): string {
  if (score >= 0.9) return "#10b981";
  if (score >= 0.75) return "#4f8eff";
  if (score >= 0.6) return "#f59e0b";
  return "#8b90a0";
}

export default function SourcesPanel() {
  const { sources } = useResearchStore();

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="text-[10px] font-semibold tracking-widest text-text3 uppercase">Sources</div>
        <div className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent/10 text-accent">
          {sources.length}
        </div>
      </div>

      <div className="overflow-y-auto">
        {sources.length === 0 ? (
          <div className="p-4 text-[11px] text-text3">No sources collected</div>
        ) : (
          sources.map((s, i) => (
            <a
              key={i}
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-3 border-b border-border hover:bg-bg2 transition-colors"
            >
              <div className="text-[11px] font-medium text-text leading-snug mb-1 line-clamp-2">
                {s.title || "Untitled"}
              </div>
              <div className="text-[10px] text-text3 font-mono mb-1.5 truncate">
                ⌀ {s.domain || s.url.slice(0, 30)}
              </div>
              <div
                className="inline-flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded font-mono"
                style={{
                  background: `${scoreColor(s.score)}18`,
                  color: scoreColor(s.score),
                }}
              >
                ★ {Math.round(s.score * 100)}% relevance
              </div>
            </a>
          ))
        )}
      </div>
    </div>
  );
}
