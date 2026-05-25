"use client";
import { useResearchStore } from "@/store/researchStore";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

async function exportToPDF(markdown: string) {
  const html2pdf = (await import("html2pdf.js")).default;
  const container = document.createElement("div");
  container.className = "report-body";
  container.style.cssText = "padding:32px;font-family:system-ui;color:#111;background:#fff;max-width:800px";
  container.innerHTML = `<h1 style="font-size:22px;margin-bottom:16px">Atlas Research Report</h1>${markdown}`;
  document.body.appendChild(container);
  await html2pdf()
    .set({ margin: 16, filename: "atlas-report.pdf", image: { type: "jpeg", quality: 0.98 } })
    .from(container)
    .save();
  document.body.removeChild(container);
}

export default function ReportViewer() {
  const { report, sources } = useResearchStore();

  if (!report) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-10">
        <div className="text-5xl opacity-40">📄</div>
        <div className="text-[14px] font-medium text-text2">No report yet</div>
        <div className="text-[12px] text-text3 max-w-[260px] leading-relaxed">
          Complete a research session to generate a structured report.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-5">
        <div className="report-body max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
        </div>
      </div>

      {/* Export bar */}
      <div className="flex gap-2 p-3 border-t border-border bg-bg1">
        <button
          onClick={() => exportToPDF(report)}
          className="flex-1 h-8 flex items-center justify-center gap-1.5 text-[11px] font-medium
            bg-bg2 border border-border2 rounded-lg text-text hover:bg-bg3 transition-colors"
        >
          📄 Export PDF
        </button>
        <button
          onClick={() => navigator.clipboard.writeText(report)}
          className="flex-1 h-8 flex items-center justify-center gap-1.5 text-[11px] font-medium
            bg-bg2 border border-border2 rounded-lg text-text hover:bg-bg3 transition-colors"
        >
          📋 Copy MD
        </button>
      </div>
    </div>
  );
}
