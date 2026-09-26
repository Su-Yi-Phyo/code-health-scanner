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

interface FolderNodeProps {
  folderPath: string;
  folderScore: number;
  files: FileRecord[];
  onSelectFile: (file: FileRecord) => void;
  selectedId: string | null;
}

function FolderNode({ folderPath, folderScore, files, onSelectFile, selectedId }: FolderNodeProps) {
  const [open, setOpen] = useState(true);
  const level = scoreToLevel(folderScore);
  const color = getRiskColor(level);

  // Folder name = last segment
  const folderName = folderPath.split("/").pop() ?? folderPath;
  const folderPrefix = folderPath.split("/").slice(0, -1).join("/");

  return (
    <div>
      {/* Folder header */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="group flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition hover:bg-slate-800/50"
      >
        {/* Chevron */}
        <svg
          width="12" height="12" viewBox="0 0 12 12" fill="none"
          className={`shrink-0 transition-transform text-slate-600 ${open ? "rotate-90" : ""}`}
        >
          <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>

        {/* Folder icon */}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" className="shrink-0">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
        </svg>

        {/* Path */}
        <span className="flex-1 font-mono text-xs text-slate-400 group-hover:text-slate-200">
          {folderPrefix && <span className="text-slate-600">{folderPrefix}/</span>}
          <span className="text-slate-300">{folderName}</span>
        </span>

        {/* Score */}
        <span className="font-mono text-xs font-bold mr-2" style={{ color }}>
          {folderScore.toFixed(1)}
        </span>

        <RiskBadge level={level} />
      </button>

      {/* Files */}
      {open && (
        <div className="ml-5 border-l border-slate-800 pl-3 mt-1 mb-2 flex flex-col gap-0.5">
          {files.map((file) => (
            <FileRow
              key={file.id}
              file={file}
              onSelect={onSelectFile}
              isSelected={selectedId === file.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}

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
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="shrink-0 text-slate-600">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>

      {/* File name */}
      <span className={`flex-1 truncate font-mono text-xs ${isSelected ? "text-indigo-300" : "text-slate-400 group-hover:text-slate-200"}`}>
        {fileName}
      </span>

      {/* Issue count hint */}
      {issueCount > 0 && (
        <span className="font-mono text-[10px] text-slate-600 mr-1">
          {issueCount} issue{issueCount !== 1 ? "s" : ""}
        </span>
      )}

      {/* Score */}
      <span className="font-mono text-xs font-bold w-8 text-right" style={{ color }}>
        {file.risk_score.toFixed(0)}
      </span>

      <RiskBadge level={level} />
    </button>
  );
}

export default function RepositoryExplorer({ result, onSelectFile, selectedId }: RepositoryExplorerProps) {
  // Build a map: folder → files belonging to it
  const folderFileMap: Record<string, FileRecord[]> = {};

  for (const folderPath of Object.keys(result.folderScores)) {
    folderFileMap[folderPath] = result.files.filter((f) =>
      f.file_path.startsWith(folderPath + "/") || f.file_path.startsWith(folderPath)
    );
  }

  // Files not belonging to any tracked folder
  const trackedFiles = new Set(Object.values(folderFileMap).flat().map((f) => f.id));
  const rootFiles = result.files.filter((f) => !trackedFiles.has(f.id));

  // Sort folders by score descending
  const sortedFolders = Object.entries(result.folderScores).sort(([, a], [, b]) => b - a);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
          Codebase Explorer
        </h2>
        <span className="font-mono text-xs text-slate-600">
          {result.files.length} files · {Object.keys(result.folderScores).length} folders
        </span>
      </div>

      <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
        {/* Column headers */}
        <div className="mb-2 flex items-center gap-2 px-3 pb-2 border-b border-slate-800">
          <span className="flex-1 font-mono text-[10px] uppercase tracking-widest text-slate-600">Path</span>
          <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mr-10">Score</span>
          <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600 w-16 text-right">Level</span>
        </div>

        <div className="flex flex-col gap-1">
          {sortedFolders.map(([folderPath, score]) => (
            <FolderNode
              key={folderPath}
              folderPath={folderPath}
              folderScore={score}
              files={folderFileMap[folderPath] ?? []}
              onSelectFile={onSelectFile}
              selectedId={selectedId}
            />
          ))}

          {/* Root-level files */}
          {rootFiles.length > 0 && (
            <div className="mt-2 pl-1">
              <p className="font-mono text-[10px] text-slate-600 mb-1 px-3">root</p>
              {rootFiles.map((file) => (
                <FileRow
                  key={file.id}
                  file={file}
                  onSelect={onSelectFile}
                  isSelected={selectedId === file.id}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
