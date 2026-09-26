"use client";

import { useRef, useState } from "react";
import ScannerHero from "@/components/ScannerHero";
import RepositoryOverview from "@/components/RepositoryOverview";
import RepositoryExplorer from "@/components/RepositoryExplorer";
import PriorityFiles from "@/components/PriorityFiles";
import FileDetail from "@/components/FileDetail";
import {
  runScan,
  explainFile,
  type ScanResult,
  type FileRecord,
  type ExplainResponse,
} from "@/lib/api";

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
  const [aiExplanation, setAiExplanation] = useState<ExplainResponse | null>(null);
  const [isExplaining, setIsExplaining] = useState(false);
  const [explainError, setExplainError] = useState<string | null>(null);
  const [showBobModal, setShowBobModal] = useState(false);
  const [bobPrompt, setBobPrompt] = useState("");
  const [bobPromptCopied, setBobPromptCopied] = useState(false);

  // Ref for the selected-file analysis panel so we can scroll to it
  const fileDetailRef = useRef<HTMLDivElement>(null);

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

  async function handleSelectFile(file: FileRecord) {
    // Clicking the selected file again closes it.
    if (selectedFile?.id === file.id) {
      setSelectedFile(null);
      setAiExplanation(null);
      setExplainError(null);
      return;
    }

    setSelectedFile(file);
    setAiExplanation(null);
    setExplainError(null);

    // Scroll to the file-detail panel smoothly
    requestAnimationFrame(() => {
      fileDetailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    if (!result) return;

    setIsExplaining(true);

    try {
      const explanation = await explainFile(result.repositoryUrl, file.file_path);
      setAiExplanation(explanation);
    } catch (err: unknown) {
      setExplainError(
        err instanceof Error ? err.message : "Unable to generate AI explanation."
      );
    } finally {
      setIsExplaining(false);
    }
  }

  function handleDeepAnalyze() {
    if (!selectedFile || !result) return;

    const duplicateCount = selectedFile.issues.duplicates.length;
    const deadCodeCount = selectedFile.issues.dead_code.length;

    const prompt = `Please analyze this file more deeply in the context of the full repository.

    Repository: ${result.repositoryUrl}
    File: ${selectedFile.file_path}
    Language: ${selectedFile.language}
    Risk score: ${selectedFile.risk_score}/100

    CodePulse scanner findings:
    - Duplicate code instances: ${duplicateCount}
    - Dead code instances: ${deadCodeCount}

    Please inspect this file and its related files in the repository. Explain why these issues matter, identify relevant dependencies or architectural problems, and recommend a safe refactoring approach.`;

    setBobPrompt(prompt);
    setBobPromptCopied(false);
    setShowBobModal(true);
  }

  async function handleCopyBobPrompt() {
    try {
      await navigator.clipboard.writeText(bobPrompt);
      setBobPromptCopied(true);
    } catch {
      alert("Unable to copy the Bob prompt.");
    }
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
              Scanning&hellip;
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
              <span className="font-mono text-xs text-slate-400">Analyzing repository&hellip;</span>
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

            {/* 1. Repository summary */}
            <section>
              <RepositoryOverview result={result} />
            </section>

            {/* 2. Codebase Explorer — full width */}
            <section>
              <RepositoryExplorer
                result={result}
                onSelectFile={handleSelectFile}
                selectedId={selectedFile?.id ?? null}
              />
            </section>

            {/* 3. Selected file analysis (overview + IBM Bob + issues) */}
            <section ref={fileDetailRef}>
              {selectedFile ? (
                <div className="flex flex-col gap-5">
                  {/* Section label */}
                  <div className="flex items-center gap-3">
                    <span className="h-px flex-1 bg-slate-800" />
                    <h2 className="font-mono text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                      Selected File Analysis
                    </h2>
                    <span className="h-px flex-1 bg-slate-800" />
                  </div>

                  {/* Two-column on large screens: overview left, IBM Bob right */}
                  <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
                    {/* File overview metrics (left, wider) */}
                    <div className="lg:col-span-3">
                      <FileDetail file={selectedFile} />
                    </div>

                    {/* IBM Bob explanation panel (right, narrower) */}
                    <div className="lg:col-span-2">
                      <div className="rounded-xl border border-indigo-500/20 bg-slate-900/60 p-5 h-full flex flex-col">
                        <div className="mb-4">
                          <p className="font-mono text-[10px] uppercase tracking-widest text-indigo-400">
                            Code Health Explanation
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            Quick analysis powered by IBM Bob
                          </p>
                        </div>

                        <div className="flex-1 text-sm leading-6 text-slate-300">
                          {isExplaining && (
                            <div className="flex items-center gap-2 text-indigo-300">
                              <span className="h-2 w-2 animate-pulse rounded-full bg-indigo-400" />
                              IBM Bob is analyzing this file&hellip;
                            </div>
                          )}

                          {explainError && (
                            <p className="text-red-400">{explainError}</p>
                          )}

                          {!isExplaining && !explainError && aiExplanation && (
                            <div className="space-y-2">
                              {aiExplanation.explanation
                                .split(/\n+/)
                                .filter((line) => line.trim())
                                .slice(0, 5)
                                .map((line, index) => (
                                  <p key={index}>
                                    &bull; {line.replace(/^[-\u2022*]\s*/, "")}
                                  </p>
                                ))}
                            </div>
                          )}

                          {!isExplaining && !explainError && !aiExplanation && (
                            <p className="text-slate-600 text-xs">
                              Waiting for analysis&hellip;
                            </p>
                          )}
                        </div>

                        <div className="mt-5 border-t border-slate-800 pt-4">
                          <p className="mb-3 text-xs text-slate-500">
                            Need a deeper investigation or help refactoring this code?
                          </p>
                          <button
                            type="button"
                            onClick={handleDeepAnalyze}
                            className="w-full rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-4 py-2.5 text-sm font-medium text-indigo-300 transition hover:bg-indigo-500/20"
                          >
                            Analyze deeper with IBM Bob &rarr;
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                /* Placeholder when no file is selected */
                <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-700/40 bg-slate-900/20 py-10 text-center px-8">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-700">
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.35-4.35" />
                  </svg>
                  <p className="text-xs text-slate-600">
                    Select a file above to view its full analysis
                  </p>
                </div>
              )}
            </section>

            {/* 4. Priority Targets */}
            <section>
              <PriorityFiles
                files={result.files}
                onSelect={handleSelectFile}
                selectedId={selectedFile?.id ?? null}
              />
            </section>

          </div>
        )}
      </main>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800/60 py-5 text-center">
        <p className="font-mono text-xs text-slate-700">
          CodePulse &middot; Hackathon build
        </p>
      </footer>

      {/* IBM Bob handoff modal */}
      {showBobModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">

            <div className="mb-5">
              <p className="font-mono text-[10px] uppercase tracking-widest text-indigo-400">
                IBM Bob
              </p>

              <h3 className="mt-2 text-lg font-semibold text-slate-100">
                Continue your investigation
              </h3>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                CodePulse has prepared the selected file and scanner findings
                for a deeper repository-level investigation in IBM Bob.
              </p>
            </div>

            <div className="space-y-3">
              <button
                type="button"
                onClick={handleCopyBobPrompt}
                className="w-full rounded-lg bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-400"
              >
                {bobPromptCopied
                  ? "\u2713 Analysis prompt copied"
                  : "Copy analysis prompt"}
              </button>

              <a
                href="https://bob.ibm.com/docs/ide/getting-started/install"
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full rounded-lg border border-slate-700 px-4 py-2.5 text-center text-sm font-medium text-slate-300 transition hover:border-slate-600 hover:bg-slate-800"
              >
                Get IBM Bob here;
              </a>

              <button
                type="button"
                onClick={() => setShowBobModal(false)}
                className="w-full px-4 py-2 text-sm text-slate-500 transition hover:text-slate-300"
              >
                Close
              </button>
            </div>

            {bobPromptCopied && (
              <div className="mt-4 rounded-lg border border-green-500/20 bg-green-500/5 p-3">
                <p className="text-xs leading-5 text-green-400">
                  Prompt copied. Open your repository in IBM Bob and paste the
                  prompt to continue the deeper analysis.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
