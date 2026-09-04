import type { ResourceRequirement } from "@/types";

interface ResourceChartProps {
  resources: ResourceRequirement | null;
}

export function ResourceChart({ resources }: ResourceChartProps) {
  if (resources === null) {
    return (
      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Resource requirements</h2>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Hosting estimates were not included for this run.
        </p>
      </section>
    );
  }

  const tiers = [
    { label: "Minimum", data: resources.requirements.minimum },
    { label: "Optimal", data: resources.requirements.optimal },
    { label: "Maximum", data: resources.requirements.maximum },
  ];

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Resource requirements</h2>
      <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
        Deployment: {resources.deploymentType}
        {resources.hostingOption ? ` via ${resources.hostingOption}` : ""}
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {tiers.map((tier) => (
          <div key={tier.label} className="border border-zinc-200 p-3 dark:border-zinc-700">
            <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">{tier.label}</p>
            <ul className="mt-2 space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
              <li>GPU: {tier.data.gpuMemory ?? "—"}</li>
              <li>CPU cores: {tier.data.cpuCores ?? "—"}</li>
              <li>RAM: {tier.data.ramGb ? `${tier.data.ramGb} GB` : "—"}</li>
              <li>Storage: {tier.data.storageSsd ?? "—"}</li>
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
