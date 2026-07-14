"use client";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 gap-4">
      <h1 className="text-2xl font-bold text-red-400">Something went wrong</h1>
      <p className="text-gray-400">{error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 rounded bg-gray-700 text-white hover:bg-gray-600"
      >
        Try again
      </button>
    </main>
  );
}
