export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="w-full max-w-2xl">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
            Python Code Health Scanner
          </h1>

          <p className="mt-3 text-slate-600">
            Find the Python files in your repository that need attention.
          </p>
        </div>

        <div className="mt-10 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <label
            htmlFor="repository-url"
            className="text-sm font-medium text-slate-700"
          >
            Public GitHub repository URL
          </label>

          <input
            id="repository-url"
            type="url"
            placeholder="https://github.com/owner/repository"
            className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500"
          />

          <button
            type="button"
            className="mt-4 w-full rounded-lg bg-slate-900 px-4 py-3 font-medium text-white transition hover:bg-slate-700"
          >
            Analyze Repository
          </button>
        </div>
      </div>
    </main>
  );
}