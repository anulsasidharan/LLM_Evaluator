import { ModelSearch } from "@/components/ModelSearch";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col items-center gap-8 px-6 py-16">
      <div className="text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-teal-700 dark:text-teal-400">
          Uniball
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          LLM Model Evaluator
        </h1>
        <p className="mt-3 max-w-lg text-zinc-600 dark:text-zinc-400">
          Search a model, generate a structured evaluation, and compare capabilities, benchmarks,
          and hosting requirements.
        </p>
      </div>
      <ModelSearch />
    </main>
  );
}
