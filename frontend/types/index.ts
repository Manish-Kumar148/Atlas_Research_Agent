export interface AgentEvent {
  agent_id: string;
  event: "started" | "completed" | "tool_call" | "error" | "done" | "heartbeat";
  timestamp: string;
  summary: string;
  tool_calls: string[];
  data: Record<string, unknown>;
}

export interface Source {
  url: string;
  title: string;
  content?: string;
  score: number;
  domain: string;
}

export interface Finding {
  type: "finding" | "trend" | "limitation" | "metric" | "quote";
  title: string;
  text: string;
  source_url: string;
  confidence: number;
}

export interface MemoryEntry {
  content: string;
  tags: string[];
  similarity_score: number;
  session_id: string;
}

export interface ResearchSession {
  id: string;
  workspace_id: string | null;
  topic: string;
  status: "pending" | "running" | "completed" | "failed";
  agent_states: Record<string, unknown>;
  created_at: string;
  completed_at: string | null;
}

export interface ResearchReport {
  id: string;
  session_id: string;
  content_markdown: string;
  sources: Source[];
  findings: Finding[];
  confidence_score: number;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type AgentStatus = "waiting" | "active" | "done" | "error";

export interface AgentState {
  id: string;
  name: string;
  icon: string;
  color: string;
  status: AgentStatus;
  statusText: string;
}

export const AGENT_DEFINITIONS: AgentState[] = [
  { id: "task_understanding", name: "Task Understanding", icon: "🎯", color: "#4f8eff", status: "waiting", statusText: "Waiting" },
  { id: "planning",           name: "Planning Agent",    icon: "🗺️", color: "#7c3aed", status: "waiting", statusText: "Waiting" },
  { id: "web_research",       name: "Web Research",      icon: "🔍", color: "#22d3ee", status: "waiting", statusText: "Waiting" },
  { id: "knowledge_extraction",name:"Knowledge Extraction",icon:"⚙️",color: "#f59e0b", status: "waiting", statusText: "Waiting" },
  { id: "memory_agent",       name: "Memory Agent",      icon: "🧠", color: "#10b981", status: "waiting", statusText: "Waiting" },
  { id: "reflection",         name: "Reflection Agent",  icon: "🪞", color: "#ec4899", status: "waiting", statusText: "Waiting" },
  { id: "report_generation",  name: "Report Generation", icon: "📊", color: "#a78bfa", status: "waiting", statusText: "Waiting" },
];
