import { AppShell } from "@/components/app-shell";
import { Dashboard } from "@/components/dashboard";
import { ModulePage } from "@/components/module-page";

export default async function WorkspacePage({ params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await params;
  const root = path[0] ?? "dashboard";
  const slug = root === "treasury" && path[1] === "transfers" ? "transfers" : root;
  return <AppShell>{root === "dashboard" ? <Dashboard/> : <ModulePage slug={slug}/>}</AppShell>;
}

