"use client";

import dynamic from "next/dynamic";
import type { CSSProperties, ReactNode } from "react";

const LiquidGlass = dynamic(() => import("liquid-glass-react"), { ssr: false });

type Variant = "subtle" | "panel" | "floating" | "interactive" | "highlight";
const config: Record<Variant, { displacementScale: number; blurAmount: number; saturation: number; aberrationIntensity: number; elasticity: number }> = {
  subtle: { displacementScale: 18, blurAmount: 0.08, saturation: 110, aberrationIntensity: 0.35, elasticity: 0 },
  panel: { displacementScale: 28, blurAmount: 0.1, saturation: 120, aberrationIntensity: 0.6, elasticity: 0.04 },
  floating: { displacementScale: 42, blurAmount: 0.12, saturation: 130, aberrationIntensity: 0.9, elasticity: 0.1 },
  interactive: { displacementScale: 52, blurAmount: 0.09, saturation: 135, aberrationIntensity: 1.1, elasticity: 0.18 },
  highlight: { displacementScale: 58, blurAmount: 0.12, saturation: 140, aberrationIntensity: 1.2, elasticity: 0.12 }
};

export function GlobalGlass({ children, variant = "panel", radius = 20, interactive = false, className = "", style }: { children: ReactNode; variant?: Variant; radius?: number; interactive?: boolean; className?: string; style?: CSSProperties }) {
  const values = config[interactive ? "interactive" : variant];
  return <div className={`global-glass-fallback ${className}`} style={{ borderRadius: radius, ...style }}><LiquidGlass {...values} cornerRadius={radius} padding="0" mode="standard" className="global-glass-liquid">{children}</LiquidGlass></div>;
}

