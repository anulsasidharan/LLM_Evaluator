interface CapabilityTableProps {
  capabilities: Record<string, unknown>;
  flaws: string[];
}

export function CapabilityTable({ capabilities, flaws }: CapabilityTableProps) {
  const entries = Object.entries(capabilities);

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Capabilities</h2>
      {entries.length === 0 ? (
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Capability matrix will appear once data sources are connected.
        </p>
      ) : (
        <table className="mt-3 w-full text-left text-sm">
          <thead>
            <tr className="border-b border-zinc-200 dark:border-zinc-700">
              <th className="py-2">Domain</th>
              <th className="py-2">Value</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([key, value]) => (
              <tr key={key} className="border-b border-zinc-100 dark:border-zinc-800">
                <td className="py-2 font-medium">{key}</td>
                <td className="py-2">{String(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {flaws.length > 0 ? (
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">Known limitations</h3>
          <ul className="mt-2 list-disc pl-5 text-sm text-zinc-700 dark:text-zinc-300">
            {flaws.map((flaw) => (
              <li key={flaw}>{flaw}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
