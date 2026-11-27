import React, { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API ?? '/api'   // proxied to the FastAPI service (services/api)
const ORGS = [
  { id: 'edmhs_org', label: 'EDMHS.org (nonprofit)', type: 'nonprofit' },
  { id: 'edm_health_services_llc', label: 'EDM Health Services, LLC (for-profit)', type: 'for_profit' },
]
const PROGRAMS = [{ id: 'ict', label: 'Inner Combat Training' }, { id: 'pmsg', label: 'Pain Management Support Group' }, { id: 'kata', label: 'KATA platform' }]

function money(n) { return n == null ? '—' : '$' + Number(n).toLocaleString() }

function Analyzer({ org, program }) {
  const [file, setFile] = useState(null)
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  async function run() {
    if (!file) return
    setBusy(true); setErr(''); setRes(null)
    const fd = new FormData(); fd.append('file', file)
    try {
      const r = await fetch(`${API}/gpcs/crosswalk?org=${org}&program=${program}`, { method: 'POST', body: fd })
      if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
      setRes(await r.json())
    } catch (e) { setErr(String(e)) } finally { setBusy(false) }
  }
  const s = res?.solicitation, cw = res?.crosswalk
  return (
    <section>
      <h2>1 · Read the solicitation</h2>
      <p className="muted">Upload a Grants.gov listing, forecast or full NOFO (PDF or text).</p>
      <div className="row">
        <input type="file" accept=".pdf,.txt,.md" onChange={e => setFile(e.target.files[0])} />
        <button onClick={run} disabled={!file || busy}>{busy ? 'Reading…' : 'Analyze + crosswalk'}</button>
      </div>
      {err && <p className="error">{err}</p>}
      {s && (
        <>
          <div className="tiles">
            <div><b>{s.opportunity_number}</b><span>{s.status}</span></div>
            <div><b>{money(s.award_ceiling)}</b><span>ceiling{s.implied_years > 1.2 ? ` · ~${Math.round(s.implied_years)} yrs` : ''}</span></div>
            <div><b>{s.expected_awards ?? '—'}</b><span>awards · {money(s.total_funding)}</span></div>
            <div><b>{s.dates?.due ?? '—'}</b><span>due</span></div>
          </div>
          <h3>{s.title}</h3>
          {cw.flags.length > 0 && <ul className="flags">{cw.flags.map((f, i) => <li key={i} className={f.startsWith('BLOCKER') ? 'blocker' : ''}>{f}</li>)}</ul>}
          <h3>Requirements → package components</h3>
          <div className="tbl"><table>
            <thead><tr><th>#</th><th>Requirement</th><th>Components</th><th>Status</th></tr></thead>
            <tbody>{cw.rows.map((r, i) => (
              <tr key={i}><td>{i + 1}</td><td>{r.requirement}</td><td>{r.components.join(', ') || '—'}</td><td><span className={'st ' + r.status.replace(/\s/g, '-')}>{r.status}</span></td></tr>
            ))}</tbody>
          </table></div>
          <h3>Package: {cw.package}</h3>
          <div className="tbl"><table>
            <thead><tr><th>Component</th><th>Kind</th><th>KB coverage</th><th>Missing</th></tr></thead>
            <tbody>{Object.entries(cw.component_status).map(([id, c]) => (
              <tr key={id}><td>{c.title}{c.required ? '' : ' (optional)'}</td><td>{c.kind}</td>
                <td><meter min="0" max="1" value={c.coverage} /> {Math.round(c.coverage * 100)}%</td><td>{c.missing.join(', ') || '—'}</td></tr>
            ))}</tbody>
          </table></div>
        </>
      )}
    </section>
  )
}

function Intake({ type }) {
  const [q, setQ] = useState(null)
  useEffect(() => { fetch(`${API}/gpcs/intake/${type}`).then(r => r.json()).then(setQ).catch(() => setQ(null)) }, [type])
  if (!q) return <section><h2>2 · Applicant intake</h2><p className="muted">API not reachable.</p></section>
  return (
    <section>
      <h2>2 · Applicant intake ({type === 'nonprofit' ? 'nonprofit' : 'for-profit'})</h2>
      <ul className="rules">{q.rules.map(r => <li key={r}>{r}</li>)}</ul>
      <form className="intake" onSubmit={e => e.preventDefault()}>
        {q.questions.map(x => (
          <label key={x.key}>{x.prompt}{x.required && <em> *</em>}<small>{x.why}</small><input name={x.key} /></label>
        ))}
      </form>
    </section>
  )
}

export default function App() {
  const [org, setOrg] = useState(ORGS[0].id)
  const [program, setProgram] = useState('ict')
  const type = ORGS.find(o => o.id === org).type
  return (
    <>
      <header>
        <div className="wrap">
          <a className="brand" href="https://edmhs.org">EDMHS<span>.org</span></a>
          <nav><a href="https://edmhs.org">Home</a><a href="https://ict.edmhs.us">ICT</a><a href="https://kata.edmhs.us">KATA</a></nav>
        </div>
      </header>
      <main className="wrap">
        <h1>Grant Studio <small>GPCS · Python engine</small></h1>
        <div className="row">
          <label>Applicant <select value={org} onChange={e => setOrg(e.target.value)}>{ORGS.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}</select></label>
          <label>Program <select value={program} onChange={e => setProgram(e.target.value)}>{PROGRAMS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}</select></label>
        </div>
        <Analyzer org={org} program={program} />
        <Intake type={type} />
      </main>
    </>
  )
}
