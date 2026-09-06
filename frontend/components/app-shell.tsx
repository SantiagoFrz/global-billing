"use client";

import {
  ArrowsLeftRightIcon, BankIcon, BellIcon, BookOpenTextIcon, BriefcaseIcon, BuildingsIcon, CalendarDotsIcon,
  CaretDoubleLeftIcon, ChartLineUpIcon, ChecksIcon, CirclesThreePlusIcon, ClipboardTextIcon, CoinsIcon,
  CommandIcon, FileTextIcon, GearSixIcon, HouseIcon, ListIcon, MagnifyingGlassIcon, MoonIcon, ReceiptIcon,
  ScrollIcon, ShieldCheckIcon, SunIcon, UsersThreeIcon, VaultIcon, WalletIcon, XIcon
} from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { IconButton } from "./ui";

type Icon = typeof HouseIcon;
type NavItem = { href: string; label: string; icon: Icon };
const sections: { title: string; items: NavItem[] }[] = [
  { title: "Visión", items: [{ href: "/dashboard", label: "Dashboard", icon: HouseIcon }, { href: "/calendar", label: "Calendario", icon: CalendarDotsIcon }] },
  { title: "Negocio", items: [{ href: "/clients", label: "Clientes", icon: BuildingsIcon }, { href: "/projects", label: "Proyectos", icon: BriefcaseIcon }, { href: "/contracts", label: "Contratos", icon: ScrollIcon }] },
  { title: "Flujo financiero", items: [{ href: "/billing", label: "Cobros", icon: ReceiptIcon }, { href: "/payments", label: "Pagos", icon: WalletIcon }, { href: "/expenses", label: "Gastos", icon: CoinsIcon }, { href: "/provisions", label: "Provisiones", icon: VaultIcon }, { href: "/funds", label: "Fondos", icon: CirclesThreePlusIcon }] },
  { title: "Tesorería", items: [{ href: "/treasury", label: "Cuentas", icon: BankIcon }, { href: "/treasury/transfers", label: "Transferencias", icon: ArrowsLeftRightIcon }, { href: "/distributions", label: "Distribuciones", icon: UsersThreeIcon }, { href: "/monthly-close", label: "Cierre mensual", icon: ChecksIcon }] },
  { title: "Control", items: [{ href: "/reports", label: "Reportes", icon: ChartLineUpIcon }, { href: "/documents", label: "Documentos", icon: FileTextIcon }, { href: "/audit", label: "Auditoría", icon: ShieldCheckIcon }, { href: "/settings", label: "Configuración", icon: GearSixIcon }] }
];

type Session = { authenticated: boolean; user?: { name: string; email: string } };
type SearchResult = { type: string; id: string; label: string; href: string };

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [theme, setTheme] = useState(() => typeof document === "undefined" ? "dark" : (document.documentElement.dataset.theme ?? "dark"));
  const session = useQuery({ queryKey: ["session"], queryFn: () => apiFetch<Session>("/api/v1/auth/session/"), retry: false });
  const search = useQuery({ queryKey: ["search", query], queryFn: () => apiFetch<SearchResult[]>(`/api/v1/search/?q=${encodeURIComponent(query)}`), enabled: query.length >= 2 });

  useEffect(() => {
    if (session.data && !session.data.authenticated) router.replace("/login");
  }, [session.data, router]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setCommandOpen(value => !value); }
      if (event.key === "Escape") setCommandOpen(false);
    };
    addEventListener("keydown", handler);
    return () => removeEventListener("keydown", handler);
  }, []);

  const current = useMemo(() => sections.flatMap(s => s.items).find(item => pathname === item.href || pathname.startsWith(item.href + "/")), [pathname]);
  const initials = (session.data?.user?.name ?? "Global Admin").split(" ").slice(0, 2).map(x => x[0]).join("").toUpperCase();
  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next); document.documentElement.dataset.theme = next; localStorage.setItem("global-billing-theme", next);
  };

  return <div className={`workspace ${collapsed ? "sidebar-collapsed" : ""}`}>
    <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`} aria-label="Navegación principal">
      <div className="brand"><Image src="/brand/global-automate.jpg" width={36} height={36} alt="Global Automate" priority /><div className="brand-copy"><div className="brand-name">GLOBAL BILLING</div><div className="brand-product">Global Automate</div></div></div>
      <nav className="nav-scroll">{sections.map(section => <div key={section.title}><div className="nav-section">{section.title}</div>{section.items.map(item => { const I = item.icon; const active = pathname === item.href || pathname.startsWith(item.href + "/"); return <Link className={`nav-item ${active ? "active" : ""}`} href={item.href} key={item.href} title={collapsed ? item.label : undefined} onClick={() => setMobileOpen(false)}><I size={17} weight={active ? "fill" : "regular"}/><span>{item.label}</span></Link>; })}</div>)}</nav>
      <div className="sidebar-footer"><button className="button secondary sidebar-toggle" onClick={() => setCollapsed(x => !x)} aria-label={collapsed ? "Expandir menú" : "Contraer menú"}><CaretDoubleLeftIcon size={15} style={{ transform: collapsed ? "rotate(180deg)" : undefined }} /><span>{collapsed ? "" : "Contraer"}</span></button></div>
    </aside>
    <header className="topbar"><div className="topbar-inner"><IconButton label="Abrir menú" className="mobile-menu" onClick={() => setMobileOpen(true)}><ListIcon size={18}/></IconButton><div className="breadcrumb">Global Billing&nbsp; / &nbsp;<strong>{current?.label ?? "Dashboard"}</strong></div><button className="search-trigger" onClick={() => setCommandOpen(true)}><MagnifyingGlassIcon size={15}/><span>Buscar en Global Billing</span><kbd>⌘ K</kbd></button><div className="topbar-spacer"/><IconButton label={theme === "dark" ? "Usar modo claro" : "Usar modo oscuro"} onClick={toggleTheme}>{theme === "dark" ? <SunIcon size={17}/> : <MoonIcon size={17}/>}</IconButton><Link href="/notifications"><IconButton label="Notificaciones"><BellIcon size={17}/></IconButton></Link><div className="avatar" title={session.data?.user?.name}>{initials}</div></div></header>
    <main>{children}</main>
    <AnimatePresence>{mobileOpen && <motion.button className="overlay" aria-label="Cerrar menú" onClick={() => setMobileOpen(false)} initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} style={{display:"block",zIndex:19}}/>}</AnimatePresence>
    <AnimatePresence>{commandOpen && <motion.div className="overlay" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} onMouseDown={e => e.target === e.currentTarget && setCommandOpen(false)}><motion.div className="modal command" initial={{y:-12,opacity:0}} animate={{y:0,opacity:1}} exit={{y:-8,opacity:0}}><div className="command-input"><CommandIcon size={19}/><input autoFocus value={query} onChange={e => setQuery(e.target.value)} placeholder="Clientes, contratos, proyectos, cuentas..." aria-label="Búsqueda global"/><IconButton label="Cerrar" onClick={() => setCommandOpen(false)}><XIcon size={16}/></IconButton></div><div className="command-results">{query.length < 2 && <div className="empty"><BookOpenTextIcon size={24}/><p>Escribe al menos dos caracteres.</p></div>}{search.isLoading && <div className="empty"><p>Buscando…</p></div>}{search.data?.map(item => <button className="command-row" key={`${item.type}-${item.id}`} onClick={() => { router.push(item.href); setCommandOpen(false); }}><ClipboardTextIcon size={17}/><span>{item.label}</span><BadgeLabel>{item.type}</BadgeLabel></button>)}{query.length >= 2 && !search.isLoading && search.data?.length === 0 && <div className="empty"><p>No encontramos coincidencias.</p></div>}</div></motion.div></motion.div>}</AnimatePresence>
  </div>;
}

function BadgeLabel({ children }: { children: React.ReactNode }) { return <span className="badge" style={{marginLeft:"auto"}}>{children}</span>; }
