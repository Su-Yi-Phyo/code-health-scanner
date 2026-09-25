"use client";

import { useState } from "react";
import ScannerHero from "@/components/ScannerHero";
import RepoHealthSummary from "@/components/RepoHealthSummary";
import PriorityFiles from "@/components/PriorityFiles";
import RiskBarChart from "@/components/RiskBarChart";
import ScatterChart from "@/components/ScatterChart";
import FileTable from "@/components/FileTable";
import FileDetail from "@/components/FileDetail";
import { MOCK_FILES, MOCK_SUMMARY, type FileRecord } from "@/lib/mockData";

// Scanning states drive the UI flow.
// Replace "scanning" + "done" side-effects with a real fetch() to the FastAPI
// backend once the backend is ready.
type ScanState = "idle" | "scanning" | "done";

export default function Home() {
  const [scanState, setScanState] = useState<ScanState>("idle");
  const [selectedFile, setSelectedFile] = useState<FileRecord | null>(null);
  // repoUrl is kept so it can later be passed to the real API call
  const [, setRepoUrl] = useState("");

  function handleScan(url: string) {
    setRepoUrl(url);
    setScanState("scanning");
    // Simulate a scan delay — replace with: const data = await fetch(`/api/scan?url=${url}`)
    setTimeout(() => {
      setScanState("done");
    }, 1800);
  }

  function handleSelectFile(file: FileRecord) {
    setSelectedFile((prev) => (prev?.id === file.id ? null : file));
  }

  const isDone = scanState === "done";
  const isScanning = scanState === "scanning";

  return (
    <div className="scanner-grid min-h-screen">
      {/* ── Top nav bar ───────────────────────────────────────────── */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-slate-800/60 bg-slate-950/80 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-2">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2">
            <polyline points="16 18 22 12 16 6" />
            <polyline points="8 6 2 12 8 18" />
          </svg>
          <span className="font-mono text-sm font-semibold text-sky-400">
            PyHealthScan
          </span>
        </div>
        <div className="flex items-center gap-3">
          {isDone && (
            <span className="flex items-center gap-1.5 rounded-full border border-green-500/20 bg-green-500/5 px-3 py-1 font-mono text-xs text-green-400">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-400" />
              Scan complete
            </span>
          )}
          {isScanning && (
            <span className="flex items-center gap-1.5 rounded-full border border-sky-500/20 bg-sky-500/5 px-3 py-1 font-mono text-xs text-sky-400">
              <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-sky-400" />
              Scanning…
            </span>
          )}
          <span className="font-mono text-xs text-slate-700">v0.1.0</span>
        </div>
      </header>

      {/* ── Main content ──────────────────────────────────────────── */}
      <main className="mx-auto w-full max-w-7xl px-4 pb-20 sm:px-6">

        {/* Hero / Scanner input */}
        <ScannerHero onScan={handleScan} isScanning={isScanning} />

        {/* ── Scanning progress indicator ─────────────────────────── */}
        {isScanning && (
          <div className="mx-auto mb-12 max-w-xl rounded-xl border border-slate-700/50 bg-slate-900/60 p-6">
            <div className="mb-3 flex items-center justify-between">
              <span className="font-mono text-xs text-slate-400">Analysing repository…</span>
              <span className="font-mono text-xs text-sky-400">
                <svg className="inline h-3 w-3 animate-spin mr-1" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a10 10 0 100 10z" />
                </svg>
                Running
              </span>
            </div>
            {/* Animated progress bar */}
            <div className="h-1 w-full overflow-hidden rounded-full bg-slate-800">
              <div className="h-full animate-pulse rounded-full bg-sky-500" style={{ width: "60%" }} />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {["Cloning repo", "AST parsing", "Radon analysis", "Ruff linting"].map((step, i) => (
                <div key={step} className="flex items-center gap-1.5">
                  <span className={`inline-block h-1.5 w-1.5 rounded-full ${i < 2 ? "bg-sky-400" : "bg-slate-700 animate-pulse"}`} />
                  <span className="font-mono text-[10px] text-slate-500">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Results dashboard ────────────────────────────────────── */}
        {isDone && (
          <div className="flex flex-col gap-10">

            {/* Repository summary stats */}
            <section>
              <RepoHealthSummary summary={MOCK_SUMMARY} />
            </section>

            {/* Priority files + File detail side-by-side */}
            <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <PriorityFiles
                files={MOCK_FILES}
                onSelect={handleSelectFile}
                selectedId={selectedFile?.id ?? null}
              />
              <FileDetail file={selectedFile} />
            </section>

            {/* Charts row */}
            <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
              <RiskBarChart
                files={MOCK_FILES}
                onSelect={handleSelectFile}
                selectedId={selectedFile?.id ?? null}
              />
              <ScatterChart
                files={MOCK_FILES}
                onSelect={handleSelectFile}
                selectedId={selectedFile?.id ?? null}
              />
            </section>

            {/* Full file table + detail panel */}
            <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <FileTable
                  files={MOCK_FILES}
                  onSelect={handleSelectFile}
                  selectedId={selectedFile?.id ?? null}
                />
              </div>
              <div>
                <div className="mb-4">
                  <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
                    File Detail
                  </h2>
                </div>
                <FileDetail file={selectedFile} />
              </div>
            </section>

          </div>
        )}
      </main>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800/60 py-5 text-center">
        <p className="font-mono text-xs text-slate-700">
          Python Code Health Scanner · Hackathon build · Mock data mode
        </p>
      </footer>
    </div>
  );
}
