import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/dynamic", () => ({
  default: () => ({ children }: { children: React.ReactNode }) => <div data-testid="liquid-glass">{children}</div>,
}));

import { GlobalGlass } from "@/components/global-glass";

describe("GlobalGlass", () => {
  it("conserva el fallback y el contenido", () => {
    const { container } = render(<GlobalGlass variant="highlight">Disponible</GlobalGlass>);
    expect(screen.getByText("Disponible")).toBeInTheDocument();
    expect(container.firstElementChild).toHaveClass("global-glass-fallback");
  });
});
