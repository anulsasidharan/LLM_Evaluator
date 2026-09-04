interface ComparisonMatrixProps {
  competitors: string[];
}

export function ComparisonMatrix({ competitors }: ComparisonMatrixProps) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Competitors</h2>
      {competitors.length === 0 ? (
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Comparable models will be listed once competitor search is connected.
        </p>
      ) : (
        <ul className="mt-2 list-disc pl-5 text-sm text-zinc-700 dark:text-zinc-300">
          {competitors.map((name) => (
            <li key={name}>{name}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
