// CodePulse — API service for the FastAPI /analyze endpoint.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ─── Raw backend types (no `id` field on files) ───────────────────────────────

export interface DuplicateIssue {
  line_start: number;
  line_end: number;
  duplicate_of: string;
}

export interface DeadCodeIssue {
  name: string;
  kind: string;
  line_start: number;
  line_end: number;
}

export interface FileIssues {
  duplicates: DuplicateIssue[];
  dead_code: DeadCodeIssue[];
}

/** Shape returned directly by the backend for each file. */
export interface FileAnalysis {
  file_path: string;
  language: string;
  line_count: number;
  risk_score: number;
  issues: FileIssues;
}

/** Shape returned directly by the backend. */
export interface AnalysisResponse {
  repositoryUrl: string;
  fileCount: number;
  repositoryScore: number;
  folderScores: Record<string, number>;
  files: FileAnalysis[];
}

// ─── App-level type (adds derived `id` for React keys / selection) ────────────

export interface FileRecord extends FileAnalysis {
  /** Derived from file_path; not sent by the backend. */
  id: string;
}

export interface ScanResult {
  repositoryUrl: string;
  fileCount: number;
  repositoryScore: number;
  folderScores: Record<string, number>;
  files: FileRecord[];
}

// ─── Normalize path separators and strip a downloaded-repo root prefix ────────

/**
 * Normalize a file path from the backend:
 * - Replace backslashes with forward slashes.
 * - Strip a leading "<reponame>/" prefix that some backends add when they
 *   download a repository into a temporary folder named after the repo.
 *   We do NOT strip meaningful path segments like "src/".
 */
export function normalizePath(
  rawPath: string,
  repositoryUrl?: string
): string {
  let path = rawPath.replace(/\\/g, "/");

  if (repositoryUrl) {
    const repoName = repositoryUrl
      .replace(/\/+$/, "")
      .split("/")
      .pop()
      ?.replace(/\.git$/, "");

    if (repoName) {
      const possiblePrefixes = [
        `${repoName}/`,
        `${repoName}-main/`,
        `${repoName}-master/`,
      ];

      for (const prefix of possiblePrefixes) {
        if (path.startsWith(prefix)) {
          path = path.slice(prefix.length);
          break;
        }
      }
    }
  }

  return path;
}

// ─── API call ─────────────────────────────────────────────────────────────────

/**
 * Send a POST /analyze request and return a ScanResult with derived ids.
 * Throws a user-friendly error string on failure.
 */
export async function runScan(repositoryUrl: string): Promise<ScanResult> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repositoryUrl }),
    });
  } catch {
    throw new Error(
      "Could not connect to the CodePulse analysis server. " +
        "Make sure the backend is running and try again."
    );
  }

  if (!response.ok) {
    // Try to extract a detail message from the response body
    let detail: string | null = null;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body?.detail)) {
        // FastAPI validation errors come as an array of objects
        detail = body.detail
          .map((e: { msg?: string }) => e.msg ?? JSON.stringify(e))
          .join("; ");
      }
    } catch {
      // ignore parse errors
    }

    if (response.status === 422) {
      throw new Error(
        detail ?? "Please enter a valid public GitHub repository URL."
      );
    }

    throw new Error(
      detail ?? "Unable to analyze this repository. Please try again."
    );
  }

  const data: AnalysisResponse = await response.json();

  // Attach a stable `id` derived from the file path so React and the
  // selection logic can key on it.
  const files: FileRecord[] = data.files.map((f) => ({
    ...f,
    file_path: normalizePath(f.file_path, data.repositoryUrl),
    id: normalizePath(f.file_path, data.repositoryUrl),
  }));

  return {
    repositoryUrl: data.repositoryUrl,
    fileCount: data.fileCount,
    repositoryScore: data.repositoryScore,
    folderScores: Object.fromEntries(
      Object.entries(data.folderScores).map(([k, v]) => [normalizePath(k), v])
    ),
    files,
  };
}

export interface ExplainResponse {
  file_path: string;
  explanation: string;
  suggestions: string[];
  model_used: string;
}

export async function explainFile(
  repositoryUrl: string,
  filePath: string
): Promise<ExplainResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/explain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        repositoryUrl,
        file_path: filePath,
      }),
    });
  } catch {
    throw new Error(
      "Could not connect to the AI explanation service."
    );
  }

  if (!response.ok) {
    let detail: string | null = null;

    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Ignore response parsing errors
    }

    throw new Error(
      detail ?? "Unable to generate an AI explanation for this file."
    );
  }

  return response.json();
}