"use client";

import { ArrowRightIcon, LockKeyIcon } from "@phosphor-icons/react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Button, Input } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [error,setError]=useState(""); const [loading,setLoading]=useState(false);
  async function submit(event: FormEvent){event.preventDefault();setLoading(true);setError("");try{const result=await apiFetch<{requires2FA:boolean}>("/api/v1/auth/login/",{method:"POST",body:JSON.stringify({email,password})});router.push(result.requires2FA?"/2fa":"/dashboard");}catch(e){setError((e as Error).message)}finally{setLoading(false)}}
  return <main className="auth-page"><section className="auth-art" aria-label="Identidad Global Automate"><div className="auth-brand"><Image src="/brand/global-automate.jpg" width={42} height={42} alt="Global Automate"/><strong>GLOBAL BILLING</strong></div><div className="auth-quote"><h2>Tu dinero, sin números mágicos.</h2><p>Contratos, cobros, reservas y distribución con trazabilidad completa para tomar decisiones con confianza.</p></div></section><section className="auth-form-wrap"><form className="auth-form" onSubmit={submit}><div className="eyebrow">ACCESO INTERNO</div><h1>Bienvenido de vuelta</h1><p className="page-subtitle">Ingresa con tu cuenta administradora.</p><div className="auth-fields"><Input id="email" label="Correo" type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} required/><Input id="password" label="Contraseña" type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required/>{error&&<div className="field-error">{error}</div>}<Button className="auth-submit" type="submit" disabled={loading}>{loading?"Verificando…":"Ingresar"}<ArrowRightIcon size={15}/></Button></div><div className="auth-foot"><LockKeyIcon size={13}/> Sesión segura · solo administradores de Global Automate</div></form></section></main>;
}

