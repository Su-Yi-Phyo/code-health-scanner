"use client";

import { useState } from "react";

interface ScannerHeroProps {
  onScan: (url: string) => void;
  isScanning: boolean;
}

const CAPABILITIES = [
  { label: "Multi-Language Analysis", desc: "Supports Python, TypeScript, JavaScript, Go, and more" },
  { label: "Duplicate Detection",     desc: "Finds repeated code blocks across your repository" },
  { label: "Dead Code Detection",     desc: "Identifies unreachable functions, classes, and variables" },
  { label: "Risk Scoring",            desc: "Composite health score per file, folder, and repository" },
];

export default function ScannerHero({ onScan, isScanning }: ScannerHeroProps) {
  const [url, setUrl] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (url.trim()) onScan(url.trim());
  }

  return (
    <section className="relative flex flex-col items-center justify-center px-6 py-24 text-center overflow-hidden">
      {/* Radial glow */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% 0%, rgba(99,102,241,0.08) 0%, transparent 70%)",
        }}
      />

      {/* Status badge */}
      <div className="mb-7 flex items-center gap-2 rounded-full border border-indigo-500/25 bg-indigo-500/8 px-4 py-1.5">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-50" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-400" />
        </span>
        <span className="font-mono text-xs tracking-widest text-indigo-400">SYSTEM READY</span>
      </div>

      {/* Wordmark */}
      <div className="mb-3 flex items-center gap-3">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="14" stroke="url(#pulse-grad)" strokeWidth="2" />
          <circle cx="16" cy="16" r="7" fill="url(#pulse-grad)" fillOpacity="0.15" />
          <circle cx="16" cy="16" r="3" fill="#818cf8" />
          <defs>
            <linearGradient id="pulse-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
              <stop stopColor="#818cf8" />
              <stop offset="1" stopColor="#6366f1" />
            </linearGradient>
          </defs>
        </svg>
        <span className="font-mono text-3xl font-bold tracking-tight text-slate-100">
          Code<span className="text-indigo-400">Pulse</span>
        </span>
      </div>

      {/* Tagline */}
      <h1 className="text-4xl font-bold tracking-tight text-slate-100 sm:text-5xl">
        Know Your Codebase.{" "}
        <span className="text-indigo-400">Fix What Matters.</span>
      </h1>

      <p className="mt-5 max-w-2xl text-base text-slate-400 sm:text-lg">
        Analyze any public GitHub repository to uncover duplicate code, dead code,
        and high-risk areas — from repository level down to individual files.
      </p>

      {/* Scan form */}
      <form onSubmit={handleSubmit} className="mt-10 w-full max-w-2xl">
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
              className="w-full rounded-lg border border-slate-700 bg-slate-900/80 py-4 pl-11 pr-4 font-mono text-sm text-slate-200 placeholder-slate-600 outline-none transition focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40"
            />
          </div>
          <button
            type="submit"
            disabled={isScanning}
            className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-8 py-4 text-sm font-bold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
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
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polygon points="5 3 19 12 5 21 5 3" fill="currentColor" stroke="none" />
                </svg>
                RUN SCAN
              </>
            )}
          </button>
        </div>
        <p className="mt-2 font-mono text-[11px] text-slate-600">
          Example: https://github.com/psf/requests
        </p>
      </form>

      {/* Capability badges */}
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {CAPABILITIES.map((c) => (
          <div
            key={c.label}
            title={c.desc}
            className="flex items-center gap-1.5 rounded-full border border-slate-700/60 bg-slate-800/50 px-3 py-1.5"
          >
            <svg width="8" height="8" viewBox="0 0 8 8">
              <circle cx="4" cy="4" r="3" fill="#818cf8" fillOpacity="0.5" />
              <circle cx="4" cy="4" r="1.5" fill="#818cf8" />
            </svg>
            <span className="font-mono text-xs text-slate-400">{c.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
