"use client";

import { useState } from "react";
import type { ScanResult, FileRecord } from "@/lib/mockData";
import { scoreToLevel, getRiskColor } from "@/lib/mockData";
import RiskBadge from "./RiskBadge";

interface RepositoryExplorerProps {
  result: ScanResult;
  onSelectFile: (file: FileRecord) => void;
  selectedId: string | null;
}

// ─── Tree data model ──────────────────────────────────────────────────────────

interface TreeFile {
  kind: "file";
  name: string;
  record: FileRecord;
}

interface TreeDir {
  kind: "dir";
  name: string;
  /** Full slash-separated path from repo root, e.g. "backend/app/ai_agent" */
  path: string;
  children: TreeNode[];
  /** Highest risk score among all descendant files (used when no folderScore). */
  maxScore: number;
}

type TreeNode = TreeFile | TreeDir;

// ─── Build the tree from a flat file list ─────────────────────────────────────

function buildTree(files: FileRecord[]): TreeNode[] {
  // Virtual root — we only return its children
  const root: TreeDir = { kind: "dir", name: "", path: "", children: [], maxScore: 0 };

  for (const record of files) {
    const parts = record.file_path.split("/");
    let node = root;

    for (let i = 0; i < parts.length - 1; i++) {
      const segment = parts[i];
      const dirPath = parts.slice(0, i + 1).join("/");
      let child = node.children.find(
        (c): c is TreeDir => c.kind === "dir" && c.name === segment
      );
      if (!child) {
        child = { kind: "dir", name: segment, path: dirPath, children: [], maxScore: 0 };
        node.children.push(child);
      }
      node = child;
    }

    node.children.push({ kind: "file", name: parts[parts.length - 1], record });
  }

  // Propagate maxScore bottom-up
  function propagate(dir: TreeDir): number {
    let max = 0;
    for (const c of dir.children) {
      if (c.kind === "file") {
        max = Math.max(max, c.record.risk_score);
      } else {
        max = Math.max(max, propagate(c));
      }
    }
    dir.maxScore = max;
    return max;
  }
  propagate(root);

  // Sort children: dirs first (by maxScore desc), then files (by risk_score desc)
  function sortChildren(dir: TreeDir) {
    dir.children.sort((a, b) => {
      if (a.kind === b.kind) {
        const scoreA = a.kind === "dir" ? a.maxScore : a.record.risk_score;
        const scoreB = b.kind === "dir" ? b.maxScore : b.record.risk_score;
        return scoreB - scoreA;
      }
      return a.kind === "dir" ? -1 : 1;
    });
    for (const c of dir.children) {
      if (c.kind === "dir") sortChildren(c);
    }
  }
  sortChildren(root);

  return root.children;
}

// ─── Determine initial open state ─────────────────────────────────────────────
// Top-level dirs: open if ≤ 3 total top-level dirs or maxScore > 50.
// Deeper dirs: collapsed by default.

function shouldOpenByDefault(depth: number, node: TreeDir, totalTopLevel: number): boolean {
  if (depth === 0) return totalTopLevel <= 3 || node.maxScore > 50;
  return false;
}

// ─── File row (unchanged visual from original) ────────────────────────────────

interface FileRowProps {
  file: FileRecord;
  onSelect: (file: FileRecord) => void;
  isSelected: boolean;
}

function FileRow({ file, onSelect, isSelected }: FileRowProps) {
  const level = scoreToLevel(file.risk_score);
  const color = getRiskColor(level);
  const fileName = file.file_path.split("/").pop() ?? file.file_path;
  const issueCount = file.issues.duplicates.length + file.issues.dead_code.length;

  return (
    <button
      onClick={() => onSelect(file)}
      className={`group flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left transition ${
        isSelected
          ? "bg-indigo-500/10 border border-indigo-500/30"
          : "hover:bg-slate-800/60 border border-transparent"
      }`}
    >
      {/* File icon */}
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        className="shrink-0 text-slate-600"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>

      {/* File name */}
      <span
        className={`flex-1 truncate font-mono text-xs ${
          isSelected ? "text-indigo-300" : "text-slate-400 group-hover:text-slate-200"
        }`}
      >
        {fileName}
      </span>

      {/* Issue count hint */}
      {issueCount > 0 && (
        <span className="font-mono text-[10px] text-slate-600 mr-1 shrink-0">
          {issueCount} issue{issueCount !== 1 ? "s" : ""}
        </span>
      )}

      {/* Score */}
      <span
        className="font-mono text-xs font-bold w-8 shrink-0 text-right"
        style={{ color }}
      >
        {file.risk_score.toFixed(0)}
      </span>

      <RiskBadge level={level} />
    </button>
  );
}

// ─── Directory node ────────────────────────────────────────────────────────────

interface DirNodeProps {
  node: TreeDir;
  folderScores: Record<string, number>;
  onSelectFile: (file: FileRecord) => void;
  selectedId: string | null;
  depth: number;
  totalTopLevel: number;
}

function DirNode({
  node,
  folderScores,
  onSelectFile,
  selectedId,
  depth,
  totalTopLevel,
}: DirNodeProps) {
  const [open, setOpen] = useState(() =>
    shouldOpenByDefault(depth, node, totalTopLevel)
  );

  // Prefer the backend folder score when available, fall back to maxScore
  const score = folderScores[node.path] ?? node.maxScore;
  const level = scoreToLevel(score);
  const color = getRiskColor(level);

  // Indentation per depth level (px)
  const indent = depth * 16;

  return (
    <div>
      {/* Folder header button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="group flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition hover:bg-slate-800/50"
        style={{ paddingLeft: `${8 + indent}px` }}
      >
        {/* Chevron */}
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          className={`shrink-0 transition-transform text-slate-600 ${open ? "rotate-90" : ""}`}
        >
          <path
            d="M4 2l4 4-4 4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>

        {/* Folder icon */}
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke={color}
          strokeWidth="1.8"
          className="shrink-0"
        >
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
        </svg>

        {/* Folder name */}
        <span className="flex-1 truncate font-mono text-xs text-slate-300 group-hover:text-slate-100">
          {node.name}/
        </span>

        {/* Score */}
        <span className="font-mono text-xs font-bold mr-2 shrink-0" style={{ color }}>
          {score.toFixed(score % 1 === 0 ? 0 : 1)}
        </span>

        <RiskBadge level={level} />
      </button>

      {/* Children */}
      {open && (
        <div
          className="border-l border-slate-800/70"
          style={{ marginLeft: `${20 + indent}px` }}
        >
          {node.children.map((child) =>
            child.kind === "dir" ? (
              <DirNode
                key={child.path}
                node={child}
                folderScores={folderScores}
                onSelectFile={onSelectFile}
                selectedId={selectedId}
                depth={depth + 1}
                totalTopLevel={totalTopLevel}
              />
            ) : (
              <div key={child.record.id} className="pl-3">
                <FileRow
                  file={child.record}
                  onSelect={onSelectFile}
                  isSelected={selectedId === child.record.id}
                />
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main export ──────────────────────────────────────────────────────────────

export default function RepositoryExplorer({
  result,
  onSelectFile,
  selectedId,
}: RepositoryExplorerProps) {
  const tree = buildTree(result.files);

  // Separate top-level dirs from root-level files
  const topDirs = tree.filter((n): n is TreeDir => n.kind === "dir");
  const rootFiles = tree.filter((n): n is TreeFile => n.kind === "file");

  return (
    <div>
      {/* Section header */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
          Codebase Explorer
        </h2>
        <span className="font-mono text-xs text-slate-600">
          {result.files.length} files &middot; {Object.keys(result.folderScores).length} folders
        </span>
      </div>

      <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
        {/* Column headers */}
        <div className="mb-2 flex items-center gap-2 px-3 pb-2 border-b border-slate-800">
          <span className="flex-1 font-mono text-[10px] uppercase tracking-widest text-slate-600">
            Path
          </span>
          <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mr-10">
            Score
          </span>
          <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600 w-16 text-right">
            Level
          </span>
        </div>

        <div className="flex flex-col gap-0.5">
          {/* Directory tree */}
          {topDirs.map((dir) => (
            <DirNode
              key={dir.path}
              node={dir}
              folderScores={result.folderScores}
              onSelectFile={onSelectFile}
              selectedId={selectedId}
              depth={0}
              totalTopLevel={topDirs.length}
            />
          ))}

          {/* Root-level files */}
          {rootFiles.length > 0 && (
            <div className="mt-2">
              <p className="font-mono text-[10px] uppercase tracking-widest text-slate-600 px-3 mb-1">
                Root Files
              </p>
              {rootFiles.map((f) => (
                <FileRow
                  key={f.record.id}
                  file={f.record}
                  onSelect={onSelectFile}
                  isSelected={selectedId === f.record.id}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
