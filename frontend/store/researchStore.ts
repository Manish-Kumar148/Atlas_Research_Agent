import { create } from "zustand";
import {
  AgentEvent,
  AgentState,
  AGENT_DEFINITIONS,
  Source,
  MemoryEntry,
} from "@/types";

export type ResearchStatus = "idle" | "running" | "completed" | "failed";

interface ResearchStore {
  // State
  topic: string;
  sessionId: string | null;
  status: ResearchStatus;
  agentStates: AgentState[];
  feedEvents: AgentEvent[];
  sources: Source[];
  memories: MemoryEntry[];
  report: string | null;
  progress: number; // 0–7

  // Actions
  setTopic: (topic: string) => void;
  setSessionId: (id: string) => void;
  setStatus: (s: ResearchStatus) => void;
  updateAgentState: (agentId: string, patch: Partial<AgentState>) => void;
  addFeedEvent: (event: AgentEvent) => void;
  addSources: (sources: Source[]) => void;
  addMemory: (entry: MemoryEntry) => void;
  setReport: (md: string) => void;
  incrementProgress: () => void;
  reset: () => void;
}

const initialAgentStates = (): AgentState[] =>
  AGENT_DEFINITIONS.map((a) => ({ ...a }));

export const useResearchStore = create<ResearchStore>((set) => ({
  topic: "",
  sessionId: null,
  status: "idle",
  agentStates: initialAgentStates(),
  feedEvents: [],
  sources: [],
  memories: [],
  report: null,
  progress: 0,

  setTopic: (topic) => set({ topic }),
  setSessionId: (id) => set({ sessionId: id }),
  setStatus: (status) => set({ status }),

  updateAgentState: (agentId, patch) =>
    set((s) => ({
      agentStates: s.agentStates.map((a) =>
        a.id === agentId ? { ...a, ...patch } : a
      ),
    })),

  addFeedEvent: (event) =>
    set((s) => ({ feedEvents: [...s.feedEvents, event] })),

  addSources: (newSources) =>
    set((s) => {
      const existingUrls = new Set(s.sources.map((x) => x.url));
      const deduped = newSources.filter((x) => !existingUrls.has(x.url));
      return { sources: [...s.sources, ...deduped] };
    }),

  addMemory: (entry) =>
    set((s) => ({ memories: [...s.memories.slice(-19), entry] })),

  setReport: (md) => set({ report: md }),

  incrementProgress: () =>
    set((s) => ({ progress: Math.min(s.progress + 1, 7) })),

  reset: () =>
    set({
      sessionId: null,
      status: "idle",
      agentStates: initialAgentStates(),
      feedEvents: [],
      sources: [],
      memories: [],
      report: null,
      progress: 0,
    }),
}));
