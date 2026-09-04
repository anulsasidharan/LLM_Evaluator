import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ModelSearch } from "@/components/ModelSearch";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/services/api", () => ({
  analyzeModel: vi.fn(),
}));

describe("ModelSearch", () => {
  it("shows a validation message when submitted empty", async () => {
    const user = userEvent.setup();
    render(<ModelSearch />);
    await user.click(screen.getByRole("button", { name: /analyze model/i }));
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a model name to analyze.");
    expect(push).not.toHaveBeenCalled();
  });
});
