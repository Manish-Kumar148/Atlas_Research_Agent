"use client";
import { useEffect, useRef, useState } from "react";
import { useResearchStore } from "@/store/researchStore";
import { connectToStream } from "@/lib/streamClient";

const EXAMPLES = [
  "AI agents for ecommerce automation",
  "LLM inference optimization techniques 2025",
  "Quantum computing for drug discovery",
  "Autonomous vehicle sensor fusion",
];

export default function ResearchInput() {
  const { topic, setTopic, setSessionId, setStatus, reset, status } = useResearchStore();
  const [loading, setLoading] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  // Settings / API key states
  const [showSettings, setShowSettings] = useState(false);
  const [openrouterKey, setOpenrouterKey] = useState("");
  const [tavilyKey, setTavilyKey] = useState("");
  const [anthropicKey, setAnthropicKey] = useState("");

  // Load API keys from localStorage on mount
  useEffect(() => {
    setOpenrouterKey(localStorage.getItem("atlas_openrouter_api_key") || "");
    setTavilyKey(localStorage.getItem("atlas_tavily_api_key") || "");
    setAnthropicKey(localStorage.getItem("atlas_anthropic_api_key") || "");
  }, []);

  const saveKey = (key: string, val: string) => {
    localStorage.setItem(key, val);
  };

  async function handleRun() {
    if (!topic.trim() || loading || status === "running") return;

    // Clean up previous stream
    if (esRef.current) { esRef.current.close(); esRef.current = null; }
    reset();
    setTopic(topic);
    setLoading(true);

    try {
      const res = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topic.trim(),
          openrouter_api_key: openrouterKey.trim() || undefined,
          tavily_api_key: tavilyKey.trim() || undefined,
          anthropic_api_key: anthropicKey.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (!data.session_id) throw new Error("No session_id returned");

      setSessionId(data.session_id);
      setStatus("running");
      esRef.current = connectToStream(data.session_id);
    } catch (err) {
      setStatus("failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-4 border-b border-border">
      <div className="text-[10px] font-semibold tracking-widest text-text3 uppercase mb-3">
        Research Objective
      </div>
      <div className="relative">
        <textarea
          className="w-full bg-bg2 border border-border2 rounded-xl p-3 pb-12 text-[13px] text-text
            placeholder-text3 resize-none outline-none leading-relaxed min-h-[100px]
            focus:border-accent/50 focus:ring-2 focus:ring-accent/10 transition-all"
          placeholder="What would you like to research? E.g. browser agents for ecommerce automation…"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && e.metaKey) handleRun(); }}
          rows={4}
        />
        <div className="absolute bottom-2.5 left-2.5 right-2.5 flex gap-1.5 items-center">
          <button
            onClick={handleRun}
            disabled={loading || status === "running" || !topic.trim()}
            className="flex-1 h-7 rounded-md text-[11px] font-semibold text-white
              bg-gradient-to-r from-accent to-accent2 disabled:opacity-40 disabled:cursor-not-allowed
              hover:opacity-90 transition-opacity"
          >
            {loading ? "Starting…" : status === "running" ? "⏳ Running…" : "▶ Run Research"}
          </button>
          <button
            onClick={() => { esRef.current?.close(); reset(); }}
            className="w-7 h-7 flex items-center justify-center rounded-md
              bg-bg3 border border-border2 text-text2 hover:text-text text-sm transition-colors"
            title="Clear"
          >✕</button>
        </div>
      </div>

      {/* Example chips */}
      <div className="flex flex-wrap gap-1 mt-2.5">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => setTopic(ex)}
            className="bg-bg3 border border-border rounded-full px-2.5 py-1 text-[10px]
              text-text2 hover:border-accent hover:text-accent hover:bg-accent/5 transition-all"
          >
            {ex}
          </button>
        ))}
      </div>

      {/* API Keys Panel */}
      <div className="mt-4 pt-3 border-t border-border">
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="flex items-center gap-1.5 text-[10px] font-semibold tracking-wider text-text2 hover:text-text transition-colors uppercase"
        >
          <span>{showSettings ? "▼" : "▶"}</span>
          <span>🔑 Custom API Keys (Optional)</span>
        </button>

        {showSettings && (
          <div className="mt-3 flex flex-col gap-2.5 bg-bg2 border border-border2 rounded-xl p-3">
            <div>
              <label className="block text-[9px] font-semibold text-text3 mb-1 uppercase tracking-wider">
                OpenRouter API Key
              </label>
              <input
                type="password"
                className="w-full bg-bg3 border border-border rounded-lg px-2.5 py-1.5 text-[11px] text-text outline-none focus:border-accent/40 transition-colors"
                placeholder="sk-or-v1-..."
                value={openrouterKey}
                onChange={(e) => {
                  setOpenrouterKey(e.target.value);
                  saveKey("atlas_openrouter_api_key", e.target.value);
                }}
              />
            </div>

            <div>
              <label className="block text-[9px] font-semibold text-text3 mb-1 uppercase tracking-wider">
                Tavily API Key
              </label>
              <input
                type="password"
                className="w-full bg-bg3 border border-border rounded-lg px-2.5 py-1.5 text-[11px] text-text outline-none focus:border-accent/40 transition-colors"
                placeholder="tvly-..."
                value={tavilyKey}
                onChange={(e) => {
                  setTavilyKey(e.target.value);
                  saveKey("atlas_tavily_api_key", e.target.value);
                }}
              />
            </div>

            <div>
              <label className="block text-[9px] font-semibold text-text3 mb-1 uppercase tracking-wider">
                Anthropic API Key (Claude)
              </label>
              <input
                type="password"
                className="w-full bg-bg3 border border-border rounded-lg px-2.5 py-1.5 text-[11px] text-text outline-none focus:border-accent/40 transition-colors"
                placeholder="sk-ant-..."
                value={anthropicKey}
                onChange={(e) => {
                  setAnthropicKey(e.target.value);
                  saveKey("atlas_anthropic_api_key", e.target.value);
                }}
              />
            </div>

            <div className="text-[9px] text-text3 leading-normal">
              Keys are stored in your browser's local storage and used locally.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
