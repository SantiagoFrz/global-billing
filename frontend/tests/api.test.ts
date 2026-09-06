import { describe, expect, it } from "vitest";
import { formatCOP, formatDate } from "@/lib/api";

describe("formatos regionales", () => {
  it("formatea pesos COP sin decimales", () => {
    const output = formatCOP(1_250_000);
    expect(output).toContain("1.250.000");
    expect(output).not.toContain(",00");
  });

  it("interpreta fechas en America/Bogota", () => {
    expect(formatDate("2026-09-06T02:00:00Z")).toMatch(/05.*sept.*2026/i);
  });
});
