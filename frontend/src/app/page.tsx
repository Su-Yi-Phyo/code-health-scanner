"use client";

import { useState } from "react";
import ScannerHero from "@/components/ScannerHero";
import RepositoryOverview from "@/components/RepositoryOverview";
import RepositoryExplorer from "@/components/RepositoryExplorer";
import PriorityFiles from "@/components/PriorityFiles";
import FileDetail from "@/components/FileDetail";
import { runScan, type ScanResult, type FileRecord } from "@/lib/api";

type ScanState = "idle" | "scanning" | "done";

// Scanning step labels — match CodePulse capabilities
const SCAN_STEPS = [
  "Cloning repository",
  "Detecting languages",
  "Finding duplicates",
  "Detecting dead code",
  "Scoring risk",
];

export default function Home() {
  const [scanState, setScanState] = useState<ScanState>("idle");
  const [selectedFile, setSelectedFile] = useState<FileRecord | null>(null);
  const [scanStep, setScanStep] = useState(0);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleScan(url: string) {
    setSelectedFile(null);
    setErrorMsg(null);
    setResult(null);
    setScanState("scanning");
    setScanStep(0);

    // Animate step indicators while the real request is in-flight
    let step = 0;
    const interval = setInterval(() => {
      step = Math.min(step + 1, SCAN_STEPS.length - 1);
      setScanStep(step);
    }, 800);

    try {
      const data = await runScan(url);
      clearInterval(interval);
      setScanStep(SCAN_STEPS.length - 1);
      setResult(data);
      setScanState("done");
    } catch (err: unknown) {
      clearInterval(interval);
      setScanState("idle");
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred. Please try again."
      );
    }
  }

  function handleSelectFile(file: FileRecord) {
    setSelectedFile((prev) => (prev?.id === file.id ? null : file));
  }

  const isDone = scanState === "done";
  const isScanning = scanState === "scanning";

  return (
    <div className="scanner-grid min-h-screen flex flex-col">
      {/* ── Nav bar ──────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-slate-800/60 bg-slate-950/85 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-2.5">
          <svg width="18" height="18" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="13" stroke="#818cf8" strokeWidth="2" />
            <circle cx="16" cy="16" r="6" fill="#818cf8" fillOpacity="0.15" />
            <circle cx="16" cy="16" r="3" fill="#818cf8" />
          </svg>
          <span className="font-mono text-sm font-bold text-slate-200 tracking-tight">
            Code<span className="text-indigo-400">Pulse</span>
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
            <span className="flex items-center gap-1.5 rounded-full border border-indigo-500/20 bg-indigo-500/5 px-3 py-1 font-mono text-xs text-indigo-400">
              <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-400" />
              Scanning…
            </span>
          )}
          <span className="font-mono text-xs text-slate-700">v0.2.0</span>
        </div>
      </header>

      {/* ── Main ──────────────────────────────────────────────────────── */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 pb-20 sm:px-6">

        {/* Hero */}
        <ScannerHero onScan={handleScan} isScanning={isScanning} />

        {/* ── Error message ──────────────────────────────────────────── */}
        {errorMsg && (
          <div className="mx-auto mb-8 max-w-xl rounded-xl border border-red-500/30 bg-red-500/5 px-5 py-4">
            <div className="flex items-start gap-3">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" className="mt-0.5 shrink-0">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <p className="font-mono text-sm text-red-400">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* ── Scanning state ─────────────────────────────────────────── */}
        {isScanning && (
          <div className="mx-auto mb-12 max-w-xl rounded-xl border border-slate-700/50 bg-slate-900/60 p-6">
            <div className="mb-3 flex items-center justify-between">
              <span className="font-mono text-xs text-slate-400">Analyzing repository…</span>
              <svg className="h-3 w-3 animate-spin text-indigo-400" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a10 10 0 100 10z" />
              </svg>
            </div>

            {/* Animated indeterminate bar */}
            <div className="h-1 w-full overflow-hidden rounded-full bg-slate-800 mb-4">
              <div className="h-full rounded-full bg-indigo-500 animate-pulse" style={{ width: "65%" }} />
            </div>

            {/* Step indicators */}
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {SCAN_STEPS.map((step, i) => (
                <div key={step} className="flex items-center gap-1.5">
                  <span
                    className={`inline-block h-1.5 w-1.5 rounded-full transition-colors ${
                      i <= scanStep ? "bg-indigo-400" : "bg-slate-700 animate-pulse"
                    }`}
                  />
                  <span className={`font-mono text-[10px] transition-colors ${i <= scanStep ? "text-slate-400" : "text-slate-600"}`}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Results dashboard ─────────────────────────────────────── */}
        {isDone && result && (
          <div className="flex flex-col gap-10">

            {/* Repository overview */}
            <section>
              <RepositoryOverview result={result} />
            </section>

            {/* Explorer + File detail — side by side on desktop */}
            <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <RepositoryExplorer
                  result={result}
                  onSelectFile={handleSelectFile}
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

            {/* Priority targets + File detail — for quick mission view */}
            <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div>
                <PriorityFiles
                  files={result.files}
                  onSelect={handleSelectFile}
                  selectedId={selectedFile?.id ?? null}
                />
              </div>
              <div>
                {/* File detail repeats here so it stays next to priority list on tablet */}
                <div className="mb-4 lg:hidden">
                  <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
                    File Detail
                  </h2>
                </div>
                <div className="lg:hidden">
                  <FileDetail file={selectedFile} />
                </div>
                {/* On large screens show a "click to explore" prompt instead */}
                <div className="hidden lg:flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-700/40 bg-slate-900/20 h-full min-h-[200px] text-center px-8">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-700">
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.35-4.35" />
                  </svg>
                  <p className="text-xs text-slate-600">
                    Select a file above to view its full analysis
                  </p>
                </div>
              </div>
            </section>

          </div>
        )}
      </main>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800/60 py-5 text-center">
        <p className="font-mono text-xs text-slate-700">
          CodePulse · Hackathon build
        </p>
      </footer>
    </div>
  );
}
