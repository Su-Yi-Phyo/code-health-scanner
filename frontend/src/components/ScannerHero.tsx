"use client";

import { useState } from "react";

interface ScannerHeroProps {
  onScan: (url: string) => void;
  isScanning: boolean;
}

const TOOLS = [
  { label: "AST Analysis", desc: "Abstract syntax tree parsing" },
  { label: "Radon", desc: "Cyclomatic complexity" },
  { label: "Ruff", desc: "Fast Python linter" },
  { label: "Risk Scoring", desc: "Composite health index" },
];

export default function ScannerHero({ onScan, isScanning }: ScannerHeroProps) {
  const [url, setUrl] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (url.trim()) onScan(url.trim());
  }

  return (
    <section className="relative flex flex-col items-center justify-center px-6 py-20 text-center overflow-hidden">
      {/* Subtle radial glow behind heading */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 70% 40% at 50% 0%, rgba(56,189,248,0.07) 0%, transparent 70%)",
        }}
      />

      {/* System status badge */}
      <div className="mb-6 flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/5 px-4 py-1.5">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-60" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-sky-400" />
        </span>
        <span className="font-mono text-xs tracking-widest text-sky-400">
          SYSTEM READY
        </span>
      </div>

      {/* Main heading */}
      <h1 className="text-4xl font-bold tracking-tight text-slate-100 sm:text-5xl lg:text-6xl">
        Python Code{" "}
        <span className="text-sky-400">Health Scanner</span>
      </h1>

      <p className="mt-4 max-w-xl text-base text-slate-400 sm:text-lg">
        Point it at any public GitHub repository. We analyse every{" "}
        <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-sm text-sky-300">
          .py
        </code>{" "}
        file for complexity, lint violations, and structural risk — then rank
        the files that need attention most.
      </p>

      {/* Scan form */}
      <form
        onSubmit={handleSubmit}
        className="mt-10 w-full max-w-xl"
      >
        <div className="relative flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-500">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
              </svg>
            </span>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-900/80 py-3.5 pl-11 pr-4 font-mono text-sm text-slate-200 placeholder-slate-600 outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500/40"
            />
          </div>
          <button
            type="submit"
            disabled={isScanning}
            className="flex items-center justify-center gap-2 rounded-lg bg-sky-500 px-7 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isScanning ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a10 10 0 100 10z" />
                </svg>
                Scanning…
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
                Start Scan
              </>
            )}
          </button>
        </div>
      </form>

      {/* Tool badges */}
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {TOOLS.map((t) => (
          <div
            key={t.label}
            title={t.desc}
            className="flex items-center gap-1.5 rounded-full border border-slate-700/60 bg-slate-800/50 px-3 py-1"
          >
            <svg width="10" height="10" viewBox="0 0 10 10" className="text-sky-400">
              <circle cx="5" cy="5" r="4" fill="currentColor" fillOpacity="0.3" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <span className="font-mono text-xs text-slate-400">{t.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
