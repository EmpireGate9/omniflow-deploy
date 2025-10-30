import React, { useEffect, useMemo, useState } from "react";

export default function App(){
  const [baseUrl, setBaseUrl] = useState("");
  const api = useMemo(()=>{
    const root = baseUrl?.trim() || "";
    return {
      domains: `${root}/api/domains`,
      analyze: `${root}/api/analyze`,
      ingestCsv: (d)=> `${root}/api/ingest_csv?domain=${encodeURIComponent(d||"")}`,
      artifacts: `${root}/api/artifacts`,
    };
  }, [baseUrl]);

  const [tab, setTab] = useState("dashboard");
  const [domains, setDomains] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [toast, setToast] = useState("");

  const toastIt = m => { setToast(m); setTimeout(()=>setToast(""), 2500); };

  async function loadDomains(){ try{ const r=await fetch(api.domains); setDomains(await r.json()); }catch{ toastIt("تعذّر تحميل المجالات"); } }
  async function loadArtifacts(){ try{ const r=await fetch(api.artifacts); setArtifacts(await r.json()); }catch{ toastIt("تعذّر تحميل السجلات"); } }

  useEffect(()=>{ loadDomains(); loadArtifacts(); }, []);

  const bg = {background:"radial-gradient(1200px 800px at 20% -10%, #1f273e, #0b1220)", minHeight:"100vh", color:"#e5e7eb", fontFamily:"system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif"};
  const container = {maxWidth: "1100px", margin:"0 auto"};
  const glass = {border:"1px solid rgba(255,255,255,.12)", background:"rgba(255,255,255,.05)", borderRadius:20, padding:16};

  return (
    <div dir="rtl" style={bg}>
      <header style={{position:"sticky", top:0, backdropFilter:"blur(6px)", background:"rgba(15,23,42,.7)", borderBottom:"1px solid rgba(255,255,255,.1)"}}>
        <div style={{...container, padding:"8px 16px", display:"flex", alignItems:"center", color:"#cbd5e1"}}>
          <span style={{fontSize:12}}>RTL · عربية</span>
          <h1 style={{marginInlineStart:"auto", fontSize:20, fontWeight:700}}>PAI-6 — Operational AI (Elite)</h1>
        </div>
        <nav style={{...container, padding:"0 8px 12px", display:"flex", gap:8, alignItems:"center", overflowX:"auto"}}>
          {["dashboard","chat","io","performance","media"].map(key=>{
            const labels = {dashboard:"لوحة القيادة", chat:"الدردشة", io:"استيراد/تصدير", performance:"الأداء", media:"وسائط"};
            const active = tab===key;
            return (
              <button key={key} onClick={()=>setTab(key)} style={{padding:"8px 12px", borderRadius:16, border:`1px solid rgba(255,255,255,${active?".3":".1"})`, color: active?"#fff":"#cbd5e1", background: active?"rgba(255,255,255,.1)":"transparent"}}>{labels[key]}</button>
            );
          })}
          <input value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="Base URL (اختياري)"
                 style={{marginInlineStart:"auto", padding:"8px 10px", border:"1px solid rgba(255,255,255,.15)", borderRadius:12, background:"rgba(15,23,42,.4)", color:"#e2e8f0", width:260}}/>
        </nav>
      </header>

      <main style={{...container, padding:"16px"}}>
        {tab==="dashboard" && (
          <div style={{display:"grid", gap:16}}>
            <div style={{display:"grid", gridTemplateColumns:"1fr 2fr", gap:16}}>
              <section style={glass}>
                <div style={{color:"#cbd5e1", fontSize:14, marginBottom:8}}>إشعارات</div>
                <ul style={{lineHeight:"28px"}}>
                  <li>تم تحديث النظام</li>
                  <li>مزامنة البيانات مكتملة</li>
                  <li>لا توجد أخطاء حاليًا</li>
                </ul>
              </section>
              <section style={glass}>
                <div style={{color:"#cbd5e1", fontSize:14, marginBottom:12}}>النظرة العامة</div>
                <div style={{display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12}}>
                  {["المشاريع","المهام","العملاء","معدل النجاح"].map((t,i)=>(
                    <div key={t} style={{border:"1px solid rgba(255,255,255,.1)", background:"rgba(2,6,23,.3)", borderRadius:16, padding:16, textAlign: i===3?'center':'start'}}>
                      <div style={{color:"#cbd5e1", fontSize:12, marginBottom:4}}>{t}</div>
                      <div style={{fontSize: i===3?28:22, fontWeight:700}}>{i===3?"0%":"0"}</div>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <section style={glass}>
              <div style={{color:"#cbd5e1", fontSize:14, marginBottom:12}}>المشاريع</div>
              <div style={{color:"#94a3b8"}}>لا توجد مشاريع</div>
            </section>
          </div>
        )}

        {tab==="chat" && <Chat api={api} reload={loadArtifacts} toast={toastIt} domains={domains} />}
        {tab==="io" && <IO api={api} reload={loadArtifacts} toast={toastIt} domains={domains} />}
        {tab==="performance" && <Performance artifacts={artifacts} />}
        {tab==="media" && <section style={glass}><div style={{color:"#cbd5e1", fontSize:14, marginBottom:8}}>وسائط</div><div style={{color:"#94a3b8"}}>قسم جاهز للتوسعة لاحقًا.</div></section>}
      </main>

      <footer style={{position:"fixed", insetInline:0, bottom:0, background:"rgba(15,23,42,.7)", borderTop:"1px solid rgba(255,255,255,.1)"}}>
        <div style={{...container, padding:"8px 16px", display:"flex", alignItems:"center", justifyContent:"space-between"}}>
          <div style={{display:"flex", gap:16}}>
            <button onClick={()=>{}} style={{color:"#e2e8f0"}}>☰</button>
            <button onClick={()=>{}} style={{color:"#e2e8f0"}}>🖼️</button>
            <button onClick={()=>setTab("performance")} style={{color:"#e2e8f0"}}>⭐</button>
            <button onClick={()=>setTab("dashboard")} style={{color:"#e2e8f0"}}>🏠</button>
          </div>
          <button onClick={loadArtifacts} style={{padding:"6px 12px", borderRadius:12, background:"#111827", color:"#fff", border:"1px solid rgba(255,255,255,.1)"}}>تحديث</button>
        </div>
      </footer>

      {toast && <div style={{position:"fixed", bottom:80, left:"50%", transform:"translateX(-50%)", background:"#000", color:"#fff", padding:"8px 16px", borderRadius:9999}}>{toast}</div>}
    </div>
  );
}

function Chat({api, reload, toast, domains}){
  const [domain, setDomain] = useState("");
  const [payload, setPayload] = useState('{"example":"payload"}');
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  async function run(){
    setBusy(true); setRes(null);
    try{
      const body = { domain: domain || (domains[0]?.code||""), payload: JSON.parse(payload||"{}") };
      const r = await fetch(api.analyze, { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(body) });
      const d = await r.json(); setRes(d); if(!r.ok) toast("خطأ في التحليل"); else toast("تمت المعالجة"); await reload();
    }catch{ toast("JSON غير صالح"); }
    setBusy(false);
  }
  const glass = {border:"1px solid rgba(255,255,255,.12)", background:"rgba(255,255,255,.05)", borderRadius:20, padding:16};
  return (
    <div style={{display:"grid", gap:16, gridTemplateColumns:"1fr 1fr"}}>
      <section style={glass}>
        <div style={{display:"flex", gap:8, alignItems:"center"}}>
          <label style={{color:"#cbd5e1", fontSize:13}}>المجال</label>
          <select value={domain} onChange={e=>setDomain(e.target.value)} style={{padding:"8px 10px", border:"1px solid rgba(255,255,255,.15)", borderRadius:12, background:"rgba(15,23,42,.4)", color:"#e2e8f0"}}>
            {domains.map(d=> <option key={d.code} value={d.code}>{d.name||d.code}</option>)}
          </select>
          <button onClick={run} disabled={busy||!domains.length} style={{marginInlineStart:"auto", padding:"8px 12px", borderRadius:12, background:"#2563eb", color:"#fff", border:"none"}}>{busy?"جارٍ...":"إرسال"}</button>
        </div>
        <textarea value={payload} onChange={e=>setPayload(e.target.value)} style={{marginTop:12, width:"100%", height:240, padding:10, border:"1px solid rgba(255,255,255,.15)", borderRadius:12, background:"rgba(15,23,42,.4)", color:"#e2e8f0", fontFamily:"monospace", fontSize:12}} />
      </section>
      <section style={glass}>
        <div style={{color:"#cbd5e1", fontSize:14, marginBottom:8}}>النتيجة</div>
        <pre style={{width:"100%", height:260, overflow:"auto", background:"rgba(2,6,23,.3)", border:"1px solid rgba(255,255,255,.1)", borderRadius:12, color:"#e2e8f0", padding:10, fontSize:12}}>{res? JSON.stringify(res,null,2):"— لا يوجد رد بعد —"}</pre>
      </section>
    </div>
  );
}

function IO({api, reload, toast, domains}){
  const [csvDomain, setCsvDomain] = useState("");
  const [file, setFile] = useState(null);
  const glass = {border:"1px solid rgba(255,255,255,.12)", background:"rgba(255,255,255,.05)", borderRadius:20, padding:16};
  async function upload(){
    if(!csvDomain) return toast("اختر المجال");
    if(!file) return toast("اختر ملف CSV");
    const fd = new FormData(); fd.append("file", file);
    const r = await fetch(api.ingestCsv(csvDomain), { method:"POST", body: fd }); const d = await r.json();
    if(r.ok){ toast(`تم رفع ${d.rows} سجلّ`); await reload(); } else toast(d.error || "فشل الرفع");
  }
  return (
    <section style={glass}>
      <div style={{display:"flex", gap:8, alignItems:"center"}}>
        <label style={{color:"#cbd5e1", fontSize:13}}>المجال</label>
        <select value={csvDomain} onChange={e=>setCsvDomain(e.target.value)} style={{padding:"8px 10px", border:"1px solid rgba(255,255,255,.15)", borderRadius:12, background:"rgba(15,23,42,.4)", color:"#e2e8f0"}}>
          <option value="">— اختر —</option>
          {domains.map(d=> <option key={d.code} value={d.code}>{d.name||d.code}</option>)}
        </select>
        <input type="file" accept=".csv" onChange={e=>setFile(e.target.files?.[0]||null)} style={{color:"#e2e8f0"}}/>
        <button onClick={upload} style={{marginInlineStart:"auto", padding:"8px 12px", borderRadius:12, background:"#059669", color:"#fff", border:"none"}}>رفع</button>
      </div>
    </section>
  );
}

function Performance({artifacts}){
  const byDomain = artifacts.reduce((acc,a)=>{ acc[a.domain]=(acc[a.domain]||0)+1; return acc; },{});
  const top = Object.entries(byDomain).sort((a,b)=>b[1]-a[1]).slice(0,6);
  const glass = {border:"1px solid rgba(255,255,255,.12)", background:"rgba(255,255,255,.05)", borderRadius:20, padding:16};
  return (
    <div style={{display:"grid", gap:16, gridTemplateColumns:"1fr 2fr"}}>
      <section style={glass}>
        <div style={{color:"#cbd5e1", fontSize:14, marginBottom:8}}>الملخص</div>
        <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:12}}>
          <div style={{border:"1px solid rgba(255,255,255,.1)", background:"rgba(2,6,23,.3)", borderRadius:16, padding:16}}>
            <div style={{color:"#cbd5e1", fontSize:12, marginBottom:4}}>السجلات</div>
            <div style={{fontSize:22, fontWeight:700}}>{artifacts.length}</div>
          </div>
          <div style={{border:"1px solid rgba(255,255,255,.1)", background:"rgba(2,6,23,.3)", borderRadius:16, padding:16}}>
            <div style={{color:"#cbd5e1", fontSize:12, marginBottom:4}}>المجالات الفعالة</div>
            <div style={{fontSize:22, fontWeight:700}}>{Object.keys(byDomain).length}</div>
          </div>
        </div>
      </section>
      <section style={glass}>
        <div style={{color:"#cbd5e1", fontSize:14, marginBottom:8}}>أكثر المجالات نشاطًا</div>
        <ul style={{listStyle:"none", padding:0, margin:0}}>
          {top.map(([k,v])=> (
            <li key={k} style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8, border:"1px solid rgba(255,255,255,.1)", background:"rgba(2,6,23,.3)", borderRadius:12, padding:"8px 12px"}}>
              <span>{k || "غير محدد"}</span><span style={{color:"#cbd5e1"}}>{v}</span>
            </li>
          ))}
          {!top.length && <div style={{color:"#94a3b8"}}>لا توجد بيانات بعد.</div>}
        </ul>
      </section>
    </div>
  );
}
