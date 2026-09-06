"use client";

import { ArchiveBoxIcon, XIcon } from "@phosphor-icons/react";
import { AnimatePresence, motion } from "motion/react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function Button({ variant = "primary", className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" }) {
  return <button className={`button ${variant} ${className}`} {...props} />;
}

export function IconButton({ label, children, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; children: ReactNode }) {
  return <button className={`icon-button ${className}`} aria-label={label} title={label} {...props}>{children}</button>;
}

export function Input({ label, error, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }) {
  return <div className="field"><label htmlFor={props.id}>{label}</label><input className="input" {...props} />{error && <span className="field-error">{error}</span>}</div>;
}

export function MoneyInput(props: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label: string; error?: string }) {
  return <Input inputMode="numeric" {...props} />;
}

export function Badge({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "success" | "warning" | "danger" }) {
  return <span className={`badge ${tone === "info" ? "" : tone}`}>{children}</span>;
}

export function Progress({ value }: { value: number }) {
  return <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value}><div className="progress-value" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>;
}

export function Panel({ title, meta, children, className = "" }: { title: string; meta?: string; children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}><div className="panel-head"><h2 className="panel-title">{title}</h2>{meta && <span className="panel-meta">{meta}</span>}</div>{children}</section>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="empty"><div className="empty-icon"><ArchiveBoxIcon size={22} /></div><h3>{title}</h3><p>{description}</p>{action}</div>;
}

export function Skeleton({ height = 20, width = "100%" }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} />;
}

export function Modal({ open, onClose, title, description, children }: { open: boolean; onClose: () => void; title: string; description?: string; children: ReactNode }) {
  return <AnimatePresence>{open && <motion.div className="overlay" role="presentation" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={e => e.target === e.currentTarget && onClose()}><motion.div className="modal" role="dialog" aria-modal="true" aria-label={title} initial={{ opacity: 0, y: 14, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 8, scale: .99 }} transition={{ duration: .18 }}><div className="modal-head"><div><h2>{title}</h2>{description && <p>{description}</p>}</div><IconButton label="Cerrar" onClick={onClose}><XIcon size={17}/></IconButton></div>{children}</motion.div></motion.div>}</AnimatePresence>;
}

export function DataTable({ columns, rows, emptyTitle = "No hay registros" }: { columns: { key: string; label: string; render?: (row: Record<string, unknown>) => ReactNode }[]; rows: Record<string, unknown>[]; emptyTitle?: string }) {
  if (!rows.length) return <EmptyState title={emptyTitle} description="Crea el primer registro para comenzar a trabajar en este módulo." />;
  return <div className="table-wrap"><table className="data-table"><thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={String(row.id ?? index)}>{columns.map(c => <td key={c.key}>{c.render ? c.render(row) : String(row[c.key] ?? "—")}</td>)}</tr>)}</tbody></table></div>;
}

export function StatusBadge({ status }: { status: string }) {
  const tone = ["paid", "active", "completed", "closed"].includes(status) ? "success" : ["overdue", "cancelled", "void"].includes(status) ? "danger" : ["pending", "due_soon", "draft", "review"].includes(status) ? "warning" : "info";
  const labels: Record<string, string> = { active: "Activo", pending: "Pendiente", paid: "Pagado", overdue: "Vencido", draft: "Borrador", review: "Por revisar", closed: "Cerrado", reopened: "Reabierto", partial: "Pago parcial" };
  return <Badge tone={tone}>{labels[status] ?? status}</Badge>;
}
