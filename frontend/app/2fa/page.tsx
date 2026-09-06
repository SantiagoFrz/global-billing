"use client";

import { ShieldCheckIcon } from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Button, Input } from "@/components/ui";
import { apiFetch } from "@/lib/api";

export default function TwoFactorPage(){const router=useRouter();const[code,setCode]=useState("");const[error,setError]=useState("");const[loading,setLoading]=useState(false);async function submit(e:FormEvent){e.preventDefault();setLoading(true);setError("");try{await apiFetch("/api/v1/auth/2fa/verify/",{method:"POST",body:JSON.stringify({code})});router.replace("/dashboard")}catch(err){setError((err as Error).message)}finally{setLoading(false)}}return <main className="auth-page"><section className="auth-art"><div className="auth-quote"><ShieldCheckIcon size={42} color="#c8acff"/><h2 style={{marginTop:16}}>Una capa más antes de entrar.</h2><p>La información financiera de Global Automate requiere una verificación adicional.</p></div></section><section className="auth-form-wrap"><form className="auth-form" onSubmit={submit}><div className="eyebrow">VERIFICACIÓN EN DOS PASOS</div><h1>Código de seguridad</h1><p className="page-subtitle">Escribe el código de 6 dígitos de tu app autenticadora o un código de respaldo.</p><div className="auth-fields"><Input id="code" label="Código" inputMode="numeric" autoComplete="one-time-code" value={code} onChange={e=>setCode(e.target.value)} required autoFocus/>{error&&<div className="field-error">{error}</div>}<Button type="submit" disabled={loading}>{loading?"Verificando…":"Verificar y entrar"}</Button></div></form></section></main>}

