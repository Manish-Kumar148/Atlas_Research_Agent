import { AgentEvent, Source } from "@/types";
import { useResearchStore } from "@/store/researchStore";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const AGENT_ORDER = [
  "task_understanding",
  "planning",
  "web_research",
  "knowledge_extraction",
  "memory_agent",
  "reflection",
  "report_generation",
];

export function connectToStream(sessionId: string): EventSource {
  const store = useResearchStore.getState();
  const url = `${BACKEND}/research/stream/${sessionId}`;
  const es = new EventSource(url);

  // Mark first agent as active immediately
  store.updateAgentState("task_understanding", {
    status: "active",
    statusText: "Analyzing intent…",
  });

  es.onmessage = (e) => {
    let event: AgentEvent;
    try {
      event = JSON.parse(e.data);
    } catch {
      return;
    }

    const { addFeedEvent, updateAgentState, addSources, addMemory, setReport, setStatus, incrementProgress } =
      useResearchStore.getState();

    // Handle terminal events
    if (event.event === "done") {
      setStatus("completed");
      es.close();

      // Fetch full report
      fetch(`${BACKEND}/research/report/${sessionId}`)
        .then((r) => r.json())
        .then((data) => {
          if (data?.content_markdown) setReport(data.content_markdown);
        })
        .catch(() => {});
      return;
    }

    if (event.event === "error") {
      addFeedEvent(event);
      if (event.agent_id) {
        updateAgentState(event.agent_id, {
          status: "error",
          statusText: event.summary.slice(0, 50),
        });
      }
      setStatus("failed");
      es.close();
      return;
    }

    if (event.event === "heartbeat") return;

    // Normal agent event
    addFeedEvent(event);

    // Mark current agent done, activate next
    const idx = AGENT_ORDER.indexOf(event.agent_id);
    updateAgentState(event.agent_id, {
      status: "done",
      statusText: event.summary.slice(0, 50),
    });
    incrementProgress();

    if (idx >= 0 && idx + 1 < AGENT_ORDER.length) {
      const nextId = AGENT_ORDER[idx + 1];
      updateAgentState(nextId, { status: "active", statusText: "Running…" });
    }

    // Extract sources from web_research events
    if (event.agent_id === "web_research" && event.data?.sources) {
      addSources(event.data.sources as Source[]);
    }

    // Extract memories from memory_agent events
    if (event.agent_id === "memory_agent" && event.data?.memory_ids) {
      const ids = event.data.memory_ids as string[];
      ids.forEach((id) =>
        addMemory({
          content: `Stored: ${id}`,
          tags: [event.agent_id],
          similarity_score: 1.0,
          session_id: sessionId,
        })
      );
    }

    // Report markdown in event data (optional early delivery)
    if (event.agent_id === "report_generation" && event.data?.report_markdown) {
      setReport(event.data.report_markdown as string);
    }
  };

  es.onerror = () => {
    const { status, setStatus } = useResearchStore.getState();
    if (status === "running") {
      // Attempt reconnect is handled by EventSource automatically
      // If permanently closed:
      setTimeout(() => {
        if (es.readyState === EventSource.CLOSED) {
          setStatus("failed");
        }
      }, 5000);
    }
  };

  return es;
}
