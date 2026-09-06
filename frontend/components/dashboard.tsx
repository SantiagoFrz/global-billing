"use client";

import { ArrowDownRightIcon, ArrowUpRightIcon, BankIcon, CalendarCheckIcon, ChartLineUpIcon, CoinsIcon, HandCoinsIcon, LockKeyIcon, ReceiptIcon, VaultIcon, WarningCircleIcon } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { apiFetch, formatCOP, formatDate, Paginated } from "@/lib/api";
import { GlobalGlass } from "./global-glass";
import { Badge, Modal, Panel, Skeleton } from "./ui";

type BreakdownLine = { label: string; amount: number; operator: "+" | "-"; href: string };
type DashboardData = { asOf: string; bankBalance: number; reserved: number; committed: number; available: number; distributable: number; receivableThisMonth: number; overdue: number; expensesDue: number; monthResult: number; breakdowns: Record<string, BreakdownLine[]> };
type Installment = { id: string; due_date: string; amount: number; balance: number; status: string };
type Provision = { id: string; name: string; target_amount: number; reserved_balance: number; remaining_amount: number; suggested_contribution: number; due_date: string; progress_percentage: number };

const metrics = [
  { key: "bankBalance", label: "Saldo bancario", icon: BankIcon, note: "Efectivo registrado en cuentas", tone: "" },
  { key: "reserved", label: "Dinero reservado", icon: LockKeyIcon, note: "No disponible para uso libre", tone: "warn" },
  { key: "committed", label: "Dinero comprometido", icon: ReceiptIcon, note: "Obligaciones y salidas aprobadas", tone: "warn" },
  { key: "available", label: "Dinero libre", icon: HandCoinsIcon, note: "Banco menos reservas y compromisos", tone: "good" },
  { key: "receivableThisMonth", label: "Por cobrar este mes", icon: CalendarCheckIcon, note: "Saldo exigible del periodo", tone: "" },
  { key: "overdue", label: "Cartera vencida", icon: WarningCircleIcon, note: "Cuotas con fecha cumplida", tone: "bad" },
  { key: "expensesDue", label: "Gastos pendientes", icon: CoinsIcon, note: "Registrados y aún no pagados", tone: "warn" },
  { key: "monthResult", label: "Resultado del mes", icon: ChartLineUpIcon, note: "Cobros recibidos menos gastos pagados", tone: "good" }
] as const;

export function Dashboard() {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: () => apiFetch<DashboardData>("/api/v1/dashboard/") });
  const installments = useQuery({ queryKey: ["installments", "upcoming"], queryFn: () => apiFetch<Paginated<Installment>>("/api/v1/installments/?ordering=due_date&page_size=5") });
  const provisions = useQuery({ queryKey: ["provisions", "critical"], queryFn: () => apiFetch<Paginated<Provision>>("/api/v1/provisions/?status=active&ordering=due_date&page_size=4") });
  const [breakdown, setBreakdown] = useState<string | null>(null);
  const data = dashboard.data;
  const maxFlow = Math.max(1, data?.receivableThisMonth ?? 0, data?.expensesDue ?? 0, Math.abs(data?.monthResult ?? 0));

  return <div className="page"><div className="page-header"><div><div className="eyebrow">CENTRO FINANCIERO</div><h1>Control real de tu dinero</h1><p className="page-subtitle">El saldo del banco es solo el comienzo. Aquí ves qué parte está reservada, comprometida y verdaderamente libre.</p></div><Badge tone="success"><span aria-hidden>●</span> Datos al día</Badge></div>
    <div className="grid metrics-grid">{metrics.map(metric => { const I = metric.icon; return <button className="metric-card" key={metric.key} onClick={() => setBreakdown(metric.key)} aria-label={`Ver detalle de ${metric.label}`}>{dashboard.isLoading ? <><Skeleton width="55%" height={12}/><div style={{height:24}}/><Skeleton width="78%" height={28}/></> : <><div className="metric-head"><span>{metric.label}</span><span className="metric-icon"><I size={16}/></span></div><div className="metric-value">{formatCOP(data?.[metric.key] ?? 0)}</div><div className={`metric-note ${metric.tone}`}>{metric.tone === "bad" ? <ArrowUpRightIcon/> : <ArrowDownRightIcon/>}{metric.note}</div></>}</button>; })}</div>
    <div className="grid dashboard-grid"><Panel title="Flujo del mes" meta="Real vs. exigible" className="cash-flow"><div className="legend"><span><i/>Ingresos / resultado</span><span><i className="out"/>Compromisos</span></div><div className="bar-chart">{[
      ["Por cobrar", data?.receivableThisMonth ?? 0, false], ["Gastos", data?.expensesDue ?? 0, true], ["Resultado", Math.abs(data?.monthResult ?? 0), (data?.monthResult ?? 0) < 0]
    ].map(([label,value,out]) => <div className="bar-group" key={String(label)}><div className={`bar ${out ? "expense" : ""}`} style={{height:`${Math.max(5,Number(value)/maxFlow*88)}%`}} title={formatCOP(Number(value))}/><span className="bar-label">{label}</span></div>)}</div></Panel>
      <Panel title="Próximos cobros" meta="Ordenados por vencimiento">{installments.isLoading ? <RowsSkeleton/> : installments.data?.results.length ? <div className="list">{installments.data.results.map(item => <Link href={`/billing/${item.id}`} className="list-row" key={item.id}><div><div className="list-title">Cuota programada</div><div className="list-subtitle"><Badge tone={item.status === "overdue" ? "danger" : "warning"}>{item.status}</Badge></div></div><div><div className="list-amount">{formatCOP(item.balance)}</div><div className="list-date">{formatDate(item.due_date)}</div></div></Link>)}</div> : <SmallEmpty text="No hay cobros programados."/>}</Panel>
    </div>
    <div className="grid dashboard-grid"><Panel title="Reservas críticas" meta="Obligaciones próximas">{provisions.isLoading ? <RowsSkeleton/> : provisions.data?.results.length ? <div className="list">{provisions.data.results.map(item => <Link href={`/provisions/${item.id}`} className="list-row" key={item.id}><div style={{minWidth:0}}><div className="list-title">{item.name}</div><div className="progress-track" style={{marginTop:9}}><div className="progress-value" style={{width:`${Math.min(100,item.progress_percentage)}%`}}/></div><div className="list-subtitle">Faltan {formatCOP(item.remaining_amount)} · sugerido {formatCOP(item.suggested_contribution)}</div></div><div><div className="list-amount">{Math.round(item.progress_percentage)}%</div><div className="list-date">{formatDate(item.due_date)}</div></div></Link>)}</div> : <SmallEmpty text="No tienes reservas activas."/>}</Panel>
      <GlobalGlass variant="highlight" interactive radius={20}><Panel title="Disponible para distribuir" meta="Después de todo"><div style={{padding:"14px 3px 7px"}}><div className="eyebrow">BASE ACTUAL</div><div className="metric-value" style={{fontSize:34}}>{formatCOP(data?.distributable ?? 0)}</div><p className="page-subtitle">Esta cifra excluye reservas, fondos y compromisos. Al ejecutar la política vigente, cada línea queda registrada y auditable.</p><button className="button secondary" style={{marginTop:13}} onClick={() => setBreakdown("available")}>Ver cómo se calcula</button></div></Panel></GlobalGlass>
    </div>
    <MoneyBreakdown open={Boolean(breakdown)} onClose={() => setBreakdown(null)} title={metrics.find(m => m.key === breakdown)?.label ?? "Detalle"} value={breakdown ? Number(data?.[breakdown as keyof DashboardData] ?? 0) : 0} lines={breakdown ? data?.breakdowns[breakdown] ?? [] : []}/>
  </div>;
}

function MoneyBreakdown({ open, onClose, title, value, lines }: { open: boolean; onClose: () => void; title: string; value: number; lines: BreakdownLine[] }) {
  return <Modal open={open} onClose={onClose} title={title} description="Cada componente enlaza al registro que lo origina."><div className="breakdown-total"><span>Total calculado</span><strong>{formatCOP(value)}</strong></div>{lines.length ? lines.map((line,index) => <div className="breakdown-row" key={`${line.label}-${index}`}><strong>{line.operator}</strong><Link href={line.href} onClick={onClose}>{line.label}</Link><strong>{formatCOP(line.amount)}</strong></div>) : <p className="page-subtitle">Esta métrica se calcula directamente desde sus registros financieros y no tiene componentes adicionales en este momento.</p>}</Modal>;
}

function RowsSkeleton(){return <div className="list">{[1,2,3].map(i=><div className="list-row" key={i}><Skeleton height={34}/><Skeleton width={80} height={24}/></div>)}</div>}
function SmallEmpty({text}:{text:string}){return <div className="empty" style={{padding:"35px 10px"}}><VaultIcon size={22}/><p>{text}</p></div>}
