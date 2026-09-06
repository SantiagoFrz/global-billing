import { AppShell } from "@/components/app-shell";
import { Dashboard } from "@/components/dashboard";
import { DetailPage } from "@/components/detail-pages";
import { ModulePage } from "@/components/module-page";

export default async function WorkspacePage({ params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await params;
  const root = path[0] ?? "dashboard";
  const slug = root === "treasury" && path[1] === "transfers" ? "transfers" : root;
  const id = root === "treasury" ? path[2] : path[1];
  return <AppShell>{root === "dashboard" ? <Dashboard/> : id ? <DetailPage slug={slug} id={id}/> : <ModulePage slug={slug}/>}</AppShell>;
}
