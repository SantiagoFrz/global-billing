import { spawn } from "node:child_process";

const args = process.argv.slice(2);
const translated = args.map((value) => value === "--host" ? "--hostname" : value).filter((value) => value !== "--strictPort");
const child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "dev", ...translated], { stdio: "inherit" });
child.on("exit", (code) => process.exit(code ?? 0));
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => child.kill(signal));

