'use client'

import { useEffect, useRef, useState } from 'react'
import {
  Activity, BarChart3, Bell, BookOpen, ChevronDown, ChevronRight,
  CircleHelp, Database, FileUp, GitCompare, LayoutDashboard,
  ListChecks, Map, RefreshCw, Search, Settings, ShieldCheck, Upload, X,
} from 'lucide-react'
import type { BenchmarkJob, CanonicalsResponse, CnmcDetail, CpseCoverage, Mapping, Overview, Review, SourceMaterial } from '../lib/api'
import { materialsApi } from '../lib/api'
import { CPSE_CONFIG, getCPSE } from '../lib/cpse'

/* ================================================================
   TYPES & NAVIGATION
   ================================================================ */

type View = 'overview' | 'upload' | 'review' | 'canonical' | 'mappings' | 'benchmark'

const nav: readonly [View, string, typeof LayoutDashboard][] = [
  ['overview', 'Overview', LayoutDashboard],
  ['upload', 'Upload & Validate', Upload],
  ['review', 'Review Queue', ListChecks],
  ['canonical', 'Canonical Registry', BookOpen],
  ['mappings', 'CPSE Mappings', GitCompare],
  ['benchmark', 'Benchmark', BarChart3],
]

/* ================================================================
   SMALL REUSABLE COMPONENTS
   ================================================================ */

function Badge({ children, tone = 'blue' }: { children: React.ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`}>{children}</span>
}

function CPSELogo({ cpse, size = 32 }: { cpse: string; size?: number }) {
  const info = getCPSE(cpse)
  return (
    <div
      className="cpse-logo"
      style={{ width: size, height: size, background: info.color, fontSize: size * 0.36 }}
      title={info.fullName}
      role="img"
      aria-label={`${info.name} logo`}
    >
      {info.initials}
    </div>
  )
}

function CPSEBadge({ cpse, compact }: { cpse: string; compact?: boolean }) {
  const info = getCPSE(cpse)
  return (
    <span className={`cpse-badge ${compact ? 'compact' : ''}`} title={info.fullName}>
      <CPSELogo cpse={cpse} size={compact ? 20 : 24} />
      <span>{info.shortCode}</span>
    </span>
  )
}

function State({ loading, error, empty, onRetry, children }: {
  loading?: boolean; error?: string; empty?: boolean; onRetry?: () => void; children?: React.ReactNode
}) {
  if (loading) return (
    <div className="card empty-panel">
      <Activity className="spin" size={25} />
      <h2>Loading registry data</h2>
      <p>Please wait while the service responds.</p>
    </div>
  )
  if (error) return (
    <div className="card empty-panel">
      <Database size={25} />
      <h2>Backend / API error</h2>
      <p>{error}</p>
      {onRetry && <button className="primary-button retry-btn" onClick={onRetry}><RefreshCw size={14} /> Retry</button>}
    </div>
  )
  if (empty) return (
    <div className="card empty-panel">
      <Database size={25} />
      <h2>No records yet</h2>
      <p>Upload a CPSE extract to populate the registry.</p>
    </div>
  )
  return <>{children}</>
}

/* ================================================================
   LAYOUT COMPONENTS
   ================================================================ */

function Sidebar({ view, setView }: { view: View; setView: (v: View) => void }) {
  return (
    <aside className="sidebar">
      <div className="india-mark"><Map size={31} strokeWidth={1.2} /></div>
      <div className="brand">
        <b>Bharath Mati</b>
        <small>Material Harmonization Across CPSEs</small>
      </div>
      <nav className="nav">
        {nav.map(([id, label, Icon]) => (
          <button key={id} className={view === id ? 'active' : ''} onClick={() => setView(id)}>
            <Icon size={17} />{label}
          </button>
        ))}
      </nav>
      <div className="nav-divider" />
      <nav className="nav">
        <button><Settings size={17} />Settings</button>
        <button><CircleHelp size={17} />Help &amp; Support</button>
      </nav>
      <div className="sidebar-bottom">
        <div className="tricolor"><i /><i /><i /></div>
        <div className="emblem">◈</div>
        <b>One Nation</b>
        <b>Common Materials</b>
        <b>Stronger Together</b>
        <small>Ministry of Heavy Industries · Government of India</small>
      </div>
    </aside>
  )
}

function Header({ view, health }: { view: View; health: string }) {
  const label = nav.find(n => n[0] === view)?.[1] ?? 'Overview'
  return (
    <header className="topbar">
      <div>
        <div className="crumb">Bharath Mati / {label}</div>
        <div className="top-title">{label}</div>
      </div>
      <div className="top-actions">
        <div className="search">
          <Search size={15} />
          <input placeholder="Search materials, codes, CPSEs..." />
        </div>
        <div className="health">
          <span className={`dot ${health !== 'operational' ? 'offline' : ''}`} />
          {health === 'operational' ? 'All systems operational' : 'Service unavailable'}
        </div>
        <Bell size={18} color="var(--muted)" />
        <div className="avatar">AD</div>
        <span className="admin-name">Admin</span>
      </div>
    </header>
  )
}

function Hero() {
  return (
    <div className="hero">
      <div>
        <div className="hero-kicker">NATIONAL MATERIAL REGISTRY</div>
        <h1>Bharath Mati</h1>
        <p>Harmonizing Materials for a Stronger, Self-Reliant India</p>
      </div>
    </div>
  )
}

/* ================================================================
   DATA DISPLAY COMPONENTS
   ================================================================ */

function Kpis({ overview }: { overview: Overview }) {
  const s = overview.statistics
  const cpseCount = overview.cpse_coverage?.length ?? 0
  const data: [string, string, string, typeof Database][] = [
    ['Total Source Records', s.records.toLocaleString(), 'Records received from CPSEs', Database],
    ['Canonical Materials (CNMC)', s.canonical_materials.toLocaleString(), 'Governed material identities', BookOpen],
    ['CPSEs Integrated', String(cpseCount), `${cpseCount} organizations connected`, GitCompare],
    ['Mapping Coverage', s.records ? `${Math.round((s.mappings / s.records) * 1000) / 10}%` : '0%', `${s.mappings.toLocaleString()} source mappings`, ShieldCheck],
  ]
  return (
    <div className="kpis">
      {data.map(([label, value, foot, Icon], i) => (
        <div className="card kpi" key={label}>
          <div className="kpi-top">
            <span>{label}</span>
            <Icon size={17} className={`kpi-icon icon-${i}`} />
          </div>
          <strong>{value}</strong>
          <small className={i === 2 ? 'positive' : 'positive'}>{foot}</small>
        </div>
      ))}
    </div>
  )
}

function Outcomes({ overview }: { overview: Overview }) {
  const counts = overview.decision_counts
  const total = Object.values(counts).reduce((a, b) => a + b, 0)
  const values: [string, number, string][] = [
    ['Equivalent', counts.EQUIVALENT || 0, 'green'],
    ['Review', counts.REVIEW || 0, 'amber'],
    ['Different', counts.DIFFERENT || 0, 'red'],
  ]
  let start = 0
  const stops = values.map(([, n, tone]) => {
    const end = total ? start + n / total * 100 : 0
    const color = tone === 'green' ? 'var(--green)' : tone === 'amber' ? 'var(--amber)' : 'var(--red)'
    const result = `${color} ${start}% ${end}%`
    start = end
    return result
  }).join(',')
  return (
    <div className="card analytics outcomes-card">
      <div className="card-head">
        <div>
          <h2>Harmonization Outcomes</h2>
          <div className="card-sub">Current registry decisions</div>
        </div>
        <Badge tone="green">{total.toLocaleString()} decisions</Badge>
      </div>
      <div className="outcomes">
        <div className="donut" style={{ background: total ? `conic-gradient(${stops})` : '#e7edf2' }}>
          <div><b>{total.toLocaleString()}</b><small>Decisions</small></div>
        </div>
        <div className="legend">
          {values.map(([name, value, tone]) => (
            <div className="legend-row" key={name}>
              <span className="legend-label"><i className={`swatch ${tone}`} />{name}</span>
              <span className="metric">{value.toLocaleString()} <small>{total ? `${(value / total * 100).toFixed(1)}%` : '0%'}</small></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function CPSECoverageBar({ coverage }: { coverage: CpseCoverage[] }) {
  if (!coverage?.length) return null
  return (
    <div className="cpse-coverage-section">
      <div className="section-label">CPSE Sources</div>
      <div className="cpse-bar">
        {coverage.map(c => {
          const info = getCPSE(c.cpse)
          return (
            <div className="cpse-source-card" key={c.cpse}>
              <CPSELogo cpse={c.cpse} size={36} />
              <div className="cpse-source-info">
                <b>{info.shortCode}</b>
                <small>{c.record_count.toLocaleString()} records</small>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ================================================================
   OVERVIEW PAGE
   ================================================================ */

function OverviewPage({ overview, setView }: { overview: Overview; setView: (v: View) => void }) {
  const actions: readonly [string, string, typeof Upload, View][] = [
    ['Upload & Validate', 'Submit CPSE material extracts', Upload, 'upload'],
    ['Review Queue', 'Resolve uncertain matches', ListChecks, 'review'],
    ['Canonical Registry', 'Browse governed CNMC identities', BookOpen, 'canonical'],
    ['CPSE Mappings', 'Inspect source relationships', GitCompare, 'mappings'],
  ]
  return (
    <>
      <Hero />
      <CPSECoverageBar coverage={overview.cpse_coverage} />
      <Kpis overview={overview} />
      <div className="analytics-grid">
        <Outcomes overview={overview} />
        <div className="card analytics">
          <div className="card-head">
            <div>
              <h2>Quality Indicators</h2>
              <div className="card-sub">Live registry health</div>
            </div>
            <ShieldCheck size={18} color="var(--green)" />
          </div>
          <div className="quality">
            <div className="quality-row">
              <div>
                <span>Pending review rate</span>
                <b>{overview.statistics.records ? `${(overview.statistics.pending_reviews / overview.statistics.records * 100).toFixed(1)}%` : '0%'}</b>
              </div>
              <div className="progress">
                <i style={{ width: `${overview.statistics.records ? Math.min(100, overview.statistics.pending_reviews / overview.statistics.records * 100) : 0}%` }} />
              </div>
            </div>
            <div className="safety">
              <span>Registry service</span>
              <Badge tone="green">OPERATIONAL</Badge>
            </div>
          </div>
        </div>
        <div className="card analytics">
          <div className="card-head">
            <div>
              <h2>Registry Activity</h2>
              <div className="card-sub">Connected service</div>
            </div>
            <Activity size={18} color="var(--blue)" />
          </div>
          <div className="timeline">
            <div className="timeline-item"><span /><div><b>Registry synchronized</b><small>{overview.statistics.records.toLocaleString()} source records available</small></div></div>
            <div className="timeline-item"><span /><div><b>Canonical identities</b><small>{overview.statistics.canonical_materials.toLocaleString()} governed materials</small></div></div>
            <div className="timeline-item"><span /><div><b>CPSE integration</b><small>{overview.cpse_coverage?.length ?? 0} organizations connected</small></div></div>
          </div>
        </div>
      </div>
      <div className="quick">
        <div className="section-label">Quick actions</div>
        <div className="quick-grid">
          {actions.map(([title, text, Icon, id]) => (
            <button className="quick-card" key={title} onClick={() => setView(id)}>
              <span className="quick-icon"><Icon size={18} /></span>
              <span><b>{title}</b><small>{text}</small></span>
              <ChevronRight size={16} />
            </button>
          ))}
        </div>
      </div>
    </>
  )
}

/* ================================================================
   UPLOAD PAGE
   ================================================================ */

function UploadPage({ onUploaded }: { onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<string>()
  const [error, setError] = useState<string>()
  const [loading, setLoading] = useState(false)
  async function submit() {
    if (!file) return
    setLoading(true); setError(undefined)
    try {
      const response = await materialsApi.upload(file)
      setResult(`${response.filename}: ${response.validation.rows} rows, ${response.validation.duplicate_rows} duplicate rows, ${response.validation.missing_descriptions} missing descriptions. ${response.validation.valid ? 'Validated and ingested.' : 'Validation failed; nothing was ingested.'}`)
      onUploaded()
    } catch (e) { setError(e instanceof Error ? e.message : 'Upload failed') }
    finally { setLoading(false) }
  }
  return (
    <>
      <div className="section-head">
        <div>
          <div className="eyebrow">Data intake</div>
          <h1>Upload &amp; Validate</h1>
          <p>Submit CSV or Excel extracts for validation and harmonization.</p>
        </div>
      </div>
      <div className="card empty-panel">
        <FileUp size={30} color="var(--blue)" />
        <h2>Choose a CPSE extract</h2>
        <p>CSV and Excel files are accepted. A description column is required.</p>
        <input type="file" accept=".csv,.xlsx,.xls" onChange={e => setFile(e.target.files?.[0] || null)} />
        <button className="primary-button" disabled={!file || loading} onClick={submit}>
          {loading ? 'Uploading…' : 'Upload and validate'}
        </button>
        {result && <p className="result success">{result}</p>}
        {error && <p className="result error">{error}</p>}
      </div>
    </>
  )
}

/* ================================================================
   REVIEW PAGE
   ================================================================ */

function ReviewPage() {
  const [items, setItems] = useState<Review[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()

  async function load() {
    setLoading(true)
    try {
      const response = await materialsApi.reviews(search)
      setItems(response.items)
      setError(undefined)
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load reviews') }
    finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [search])

  async function decide(id: string, action: 'APPROVE' | 'REJECT') {
    await materialsApi.decide(id, action)
    await load()
  }

  return (
    <>
      <div className="section-head">
        <div>
          <div className="eyebrow">Human-in-the-loop governance</div>
          <h1>Review Queue</h1>
          <p>Resolve uncertain pairwise matches before canonical publication.</p>
        </div>
        <Badge tone="amber">{items.length} pending</Badge>
      </div>
      <State loading={loading} error={error} onRetry={load} empty={!items.length}>
        <div className="card">
          <div className="filters">
            <div className="search inline">
              <Search size={15} />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search records or IDs" />
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Source record</th><th>Candidate</th><th>Confidence</th><th>Finding</th><th>Decision</th></tr></thead>
              <tbody>
                {items.map(item => (
                  <tr key={item.review_id}>
                    <td><b>{item.left_id}</b></td>
                    <td>{item.right_id}</td>
                    <td><b>{(item.ai_decision.confidence * 100).toFixed(0)}%</b></td>
                    <td>{item.ai_decision.explanation?.join('; ') || 'Uncertain match'}</td>
                    <td>
                      <button className="table-button" onClick={() => void decide(item.review_id, 'APPROVE')}>Approve</button>
                      <button className="table-button reject" onClick={() => void decide(item.review_id, 'REJECT')}>Reject</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </State>
    </>
  )
}

/* ================================================================
   CNMC DETAIL PANEL (Expanded row)
   ================================================================ */

function CnmcDetailPanel({ item, onClose }: { item: CnmcDetail; onClose: () => void }) {
  const attrs = item.harmonized_attributes || {}
  const attrEntries = Object.entries(attrs).filter(([, v]) => v != null && v !== '')

  return (
    <div className="cnmc-detail">
      <div className="cnmc-detail-header">
        <div className="cnmc-detail-title">
          <strong>{item.cnmc_id}</strong>
          <Badge tone={item.status === 'GOVERNED' ? 'green' : 'amber'}>{item.status === 'GOVERNED' ? 'Equivalent' : item.status}</Badge>
        </div>
        <button className="cnmc-close" onClick={onClose}><X size={16} /></button>
      </div>
      <div className="cnmc-detail-sub">
        <h3>{item.canonical_description || item.original_description}</h3>
        <small>Harmonized from {item.member_count} source record{item.member_count !== 1 ? 's' : ''} across {item.cpses.length} CPSE{item.cpses.length !== 1 ? 's' : ''}</small>
      </div>
      <div className="cnmc-detail-body">
        {/* Left: Harmonized Attributes */}
        <div className="cnmc-attrs-panel">
          <h4>Harmonized Attributes</h4>
          <table className="attrs-table">
            <tbody>
              {attrEntries.map(([key, value]) => (
                <tr key={key}>
                  <td className="attr-label">{key.replace(/_/g, ' ')}</td>
                  <td className="attr-value">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</td>
                </tr>
              ))}
              {item.category && (
                <tr>
                  <td className="attr-label">Category</td>
                  <td className="attr-value">{item.category}</td>
                </tr>
              )}
              {attrEntries.length === 0 && !item.category && (
                <tr><td colSpan={2} className="attr-empty">No attributes extracted</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {/* Right: Source Material Records */}
        <div className="cnmc-sources-panel">
          <div className="cnmc-sources-head">
            <h4>Source Material Records</h4>
            <Badge tone="blue">{item.member_count} record{item.member_count !== 1 ? 's' : ''}</Badge>
          </div>
          <div className="source-cards">
            {item.source_materials.map((sm: SourceMaterial) => (
              <SourceMaterialCard key={sm.record_id} sm={sm} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function SourceMaterialCard({ sm }: { sm: SourceMaterial }) {
  const info = getCPSE(sm.source)
  return (
    <div className="source-card">
      <div className="source-card-head">
        <CPSELogo cpse={sm.source} size={32} />
        <div>
          <b>{info.name}</b>
          <small>{info.fullName}</small>
        </div>
      </div>
      <div className="source-card-body">
        <div className="source-field">
          <label>Material Code</label>
          <span>{sm.material_code}</span>
        </div>
        <div className="source-field">
          <label>Original Description</label>
          <span className="source-desc">{sm.original_description}</span>
        </div>
        <div className="source-field">
          <label>Match Decision</label>
          <Badge tone={sm.decision === 'EQUIVALENT' ? 'green' : sm.decision === 'REVIEW' ? 'amber' : 'blue'}>
            {sm.decision || '—'}
          </Badge>
        </div>
        {sm.confidence != null && (
          <div className="source-field">
            <label>Match Confidence</label>
            <span className="confidence-val">{(sm.confidence * 100).toFixed(1)}%</span>
          </div>
        )}
      </div>
    </div>
  )
}

/* ================================================================
   CANONICAL REGISTRY PAGE (CNMC Master-Detail)
   ================================================================ */

function RegistryPage({ overview }: { overview: Overview | null }) {
  const [data, setData] = useState<CanonicalsResponse | null>(null)
  const [search, setSearch] = useState('')
  const [cpseFilter, setCpseFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const searchTimeout = useRef<number | undefined>(undefined)

  async function load(p = page) {
    setLoading(true)
    try {
      const response = await materialsApi.canonicals(search, cpseFilter, categoryFilter, p)
      setData(response)
      setError('')
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load registry') }
    finally { setLoading(false) }
  }

  useEffect(() => {
    window.clearTimeout(searchTimeout.current)
    searchTimeout.current = window.setTimeout(() => { setPage(1); void load(1) }, 250)
    return () => window.clearTimeout(searchTimeout.current)
  }, [search, cpseFilter, categoryFilter])

  useEffect(() => { void load() }, [page])

  function toggle(cnmcId: string) {
    setExpandedId(prev => prev === cnmcId ? null : cnmcId)
  }

  // Extract unique categories from current data for filter dropdown
  const categories = Array.from(new Set(data?.items?.map(i => i.category).filter(Boolean) ?? []))

  return (
    <>
      {/* CPSE Sources Bar */}
      {overview?.cpse_coverage && <CPSECoverageBar coverage={overview.cpse_coverage} />}

      {/* KPIs */}
      {overview && <Kpis overview={overview} />}

      {/* Section Header */}
      <div className="section-head">
        <div>
          <div className="eyebrow">Canonical Material Registry (CNMC)</div>
          <h1>Harmonized material master records across all CPSEs</h1>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="filters">
          <div className="search inline">
            <Search size={15} />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search CNMC, material, category..." />
          </div>
          {categories.length > 0 && (
            <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
              <option value="">All Categories</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          )}
          <select value={cpseFilter} onChange={e => setCpseFilter(e.target.value)}>
            <option value="">All CPSEs</option>
            {(overview?.cpse_coverage ?? []).map(c => (
              <option key={c.cpse} value={c.cpse}>{getCPSE(c.cpse).shortCode}</option>
            ))}
          </select>
        </div>

        <State loading={loading} error={error} onRetry={() => load()} empty={data?.items?.length === 0}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ width: 30 }}></th>
                  <th>CNMC ID</th>
                  <th>Canonical Material Description</th>
                  <th>Category</th>
                  <th>CPSEs</th>
                  <th>Source Records</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data?.items?.map(item => (
                  <CnmcRow key={item.cnmc_id} item={item} expanded={expandedId === item.cnmc_id} onToggle={() => toggle(item.cnmc_id)} />
                ))}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          {data && data.pages > 1 && (
            <div className="pagination">
              <span>Showing {((data.page - 1) * data.page_size) + 1}–{Math.min(data.page * data.page_size, data.total)} of {data.total.toLocaleString()} CNMCs</span>
              <div className="pagination-btns">
                <button disabled={data.page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>← Previous</button>
                <button disabled={data.page >= data.pages} onClick={() => setPage(p => p + 1)}>Next →</button>
              </div>
            </div>
          )}
        </State>
      </div>
    </>
  )
}

function CnmcRow({ item, expanded, onToggle }: { item: CnmcDetail; expanded: boolean; onToggle: () => void }) {
  const maxBadges = 3
  const visibleCpses = item.cpses.slice(0, maxBadges)
  const extraCount = item.cpses.length - maxBadges

  return (
    <>
      <tr className={`cnmc-row ${expanded ? 'expanded' : ''}`} onClick={onToggle}>
        <td className="expand-cell">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </td>
        <td><b className="link">{item.cnmc_id}</b></td>
        <td className="desc-cell">{item.canonical_description || item.original_description || '—'}</td>
        <td>{item.category || '—'}</td>
        <td>
          <div className="cpse-badges-row">
            {visibleCpses.map(c => <CPSEBadge key={c} cpse={c} compact />)}
            {extraCount > 0 && <span className="cpse-more">+{extraCount} more</span>}
          </div>
        </td>
        <td>{item.member_count}</td>
        <td><Badge tone="green">Equivalent</Badge></td>
      </tr>
      {expanded && (
        <tr className="cnmc-detail-row">
          <td colSpan={7}>
            <CnmcDetailPanel item={item} onClose={onToggle} />
          </td>
        </tr>
      )}
    </>
  )
}

/* ================================================================
   CPSE MAPPINGS PAGE
   ================================================================ */

function MappingsPage({ overview }: { overview: Overview | null }) {
  const [items, setItems] = useState<Mapping[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cpseFilter, setCpseFilter] = useState('')

  async function load() {
    setLoading(true)
    try {
      const response = await materialsApi.mappings()
      setItems(response.items)
      setError('')
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load mappings') }
    finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [])

  const filtered = cpseFilter ? items.filter(i => i.source_system === cpseFilter) : items

  // Group by CNMC for flow visualization (first 10 groups)
  const grouped: Record<string, Mapping[]> = {}
  for (const m of filtered.slice(0, 200)) {
    ;(grouped[m.cnmc_id] ??= []).push(m)
  }
  const multiGroups = Object.entries(grouped)
    .filter(([, maps]) => maps.length > 1)
    .slice(0, 6)

  return (
    <>
      <div className="section-head">
        <div>
          <div className="eyebrow">Source relationships</div>
          <h1>CPSE Mappings</h1>
          <p>Trace source material codes to governed CNMC identities.</p>
        </div>
      </div>

      {/* Mapping flow visualization */}
      {multiGroups.length > 0 && (
        <div className="mapping-flow-section">
          <div className="section-label">Harmonization Flow</div>
          <div className="mapping-flow-grid">
            {multiGroups.map(([cnmcId, maps]) => (
              <div className="mapping-flow-card card" key={cnmcId}>
                <div className="flow-sources">
                  {maps.map(m => (
                    <div key={`${m.sequence}-${m.source_code}`} className="flow-source-item">
                      <CPSEBadge cpse={m.source_system} compact />
                      <small>{m.source_code}</small>
                    </div>
                  ))}
                </div>
                <div className="flow-arrow">→</div>
                <div className="flow-cnmc">
                  <b>{cnmcId}</b>
                  <Badge tone="green">MAPPED</Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card">
        <div className="filters">
          <select value={cpseFilter} onChange={e => setCpseFilter(e.target.value)}>
            <option value="">All CPSEs</option>
            {(overview?.cpse_coverage ?? []).map(c => (
              <option key={c.cpse} value={c.cpse}>{getCPSE(c.cpse).shortCode}</option>
            ))}
          </select>
          <span className="filter-count">{filtered.length.toLocaleString()} mappings</span>
        </div>
        <State loading={loading} error={error} onRetry={load} empty={!filtered.length}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>CPSE</th>
                  <th>Source Code</th>
                  <th>CNMC Identifier</th>
                  <th>Record</th>
                  <th>Event</th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map(item => (
                  <tr key={`${item.sequence}-${item.source_code}`}>
                    <td><CPSEBadge cpse={item.source_system} compact /></td>
                    <td><b>{item.source_code}</b></td>
                    <td className="link">{item.cnmc_id}</td>
                    <td>{item.material_record_id}</td>
                    <td><Badge tone="green">{item.event_type}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </State>
      </div>
    </>
  )
}

/* ================================================================
   BENCHMARK PAGE
   ================================================================ */

function BenchmarkPage() {
  const [job, setJob] = useState<BenchmarkJob | null>(null)
  const [size, setSize] = useState(2000)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)
  const pollRef = useRef<number | undefined>(undefined)

  // Check for latest result on mount
  useEffect(() => {
    materialsApi.benchmarkLatest()
      .then(j => { if (j.status !== 'none') setJob(j) })
      .catch(() => {/* no previous result */})
    return () => window.clearTimeout(pollRef.current)
  }, [])

  async function startBenchmark() {
    setStarting(true); setError('')
    try {
      const started = await materialsApi.startBenchmark(size)
      setJob(started as unknown as BenchmarkJob)
      pollJob(started.job_id)
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed to start benchmark') }
    finally { setStarting(false) }
  }

  function pollJob(jobId: string) {
    async function check() {
      try {
        const status = await materialsApi.benchmarkStatus(jobId)
        setJob(status)
        if (status.status === 'queued' || status.status === 'running') {
          pollRef.current = window.setTimeout(check, 2000)
        }
      } catch { /* ignore polling errors */ }
    }
    pollRef.current = window.setTimeout(check, 1000)
  }

  const result = job?.result
  const isRunning = job?.status === 'queued' || job?.status === 'running'

  return (
    <>
      <div className="section-head">
        <div>
          <div className="eyebrow">Evaluation suite</div>
          <h1>Benchmark</h1>
          <p>Run harmonization benchmarks against synthetic CPSE datasets.</p>
        </div>
      </div>

      {/* Controls */}
      <div className="card benchmark-controls">
        <div className="bench-row">
          <div>
            <label>Dataset size</label>
            <select value={size} onChange={e => setSize(Number(e.target.value))} disabled={isRunning}>
              <option value={120}>Small (120)</option>
              <option value={2000}>2K records</option>
              <option value={10000}>10K records</option>
            </select>
          </div>
          <button className="primary-button" onClick={startBenchmark} disabled={isRunning || starting}>
            {starting ? 'Starting…' : isRunning ? 'Running…' : 'Start Benchmark'}
          </button>
        </div>
        {error && <p className="result error">{error}</p>}
      </div>

      {/* Status */}
      {isRunning && (
        <div className="card empty-panel">
          <Activity className="spin" size={25} />
          <h2>Benchmark {job?.status}</h2>
          <p>Processing {job?.dataset_size?.toLocaleString()} records. This may take a moment.</p>
        </div>
      )}

      {job?.status === 'failed' && (
        <div className="card empty-panel">
          <Database size={25} />
          <h2>Benchmark failed</h2>
          <p>{job.error || 'Unknown error'}</p>
        </div>
      )}

      {/* Results */}
      {job?.status === 'completed' && result && (
        <div className="card empty-panel">
          <ShieldCheck size={30} color="var(--green)" />
          <h2>Benchmark complete</h2>
          <div className="benchmark-json">
            {Object.entries(result).map(([key, value]) => (
              <div key={key}>
                <b>{key.replaceAll('_', ' ')}</b>
                <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

/* ================================================================
   MAIN PAGE
   ================================================================ */

export default function Page() {
  const [view, setView] = useState<View>('overview')
  const [overview, setOverview] = useState<Overview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [health, setHealth] = useState('operational')

  function refresh() {
    setLoading(true)
    materialsApi.overview()
      .then(data => { setOverview(data); setError(''); setHealth(data.health || 'operational') })
      .catch(e => { setError(e instanceof Error ? e.message : 'Unable to connect to registry'); setHealth('offline') })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refresh()
    materialsApi.health().then(r => setHealth(r.status)).catch(() => setHealth('offline'))
  }, [])

  let content: React.ReactNode
  if (view === 'overview') {
    if (loading) content = <State loading />
    else if (error) content = <State error={error} onRetry={refresh} />
    else if (overview) content = <OverviewPage overview={overview} setView={setView} />
    else content = <State empty />
  } else if (view === 'upload') {
    content = <UploadPage onUploaded={refresh} />
  } else if (view === 'review') {
    content = <ReviewPage />
  } else if (view === 'canonical') {
    content = <RegistryPage overview={overview} />
  } else if (view === 'mappings') {
    content = <MappingsPage overview={overview} />
  } else {
    content = <BenchmarkPage />
  }

  return (
    <div className="app">
      <Sidebar view={view} setView={setView} />
      <main className="main">
        <Header view={view} health={health} />
        <section className="content">{content}</section>
      </main>
    </div>
  )
}
