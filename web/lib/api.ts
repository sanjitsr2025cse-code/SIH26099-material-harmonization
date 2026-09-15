export type Statistics = {
  records: number
  canonical_materials: number
  mappings: number
  mapping_history: number
  pending_reviews: number
}

export type CpseCoverage = {
  cpse: string
  record_count: number
  cnmc_count: number
}

export type Overview = {
  statistics: Statistics
  decision_counts: Record<string, number>
  cpse_coverage: CpseCoverage[]
  health: string
}

export type Review = {
  review_id: string
  left_id: string
  right_id: string
  status: string
  ai_decision: { confidence: number; decision: string; explanation: string[] }
}

export type SourceMaterial = {
  record_id: string
  source: string
  material_code: string
  original_description: string
  attributes: Record<string, unknown>
  confidence: number | null
  decision: string | null
}

export type CnmcDetail = {
  cnmc_id: string
  canonical_description: string
  original_description: string
  harmonized_attributes: Record<string, unknown>
  category: string
  member_count: number
  cpses: string[]
  status: string
  source_materials: SourceMaterial[]
}

export type CanonicalsResponse = {
  items: CnmcDetail[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type Mapping = {
  source_code: string
  source_system: string
  cnmc_id: string
  material_record_id: string
  event_type: string
  sequence: number
}

export type BenchmarkJob = {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'none'
  dataset_size: number
  result: Record<string, unknown> | null
  error: string | null
  started_at: number | null
  completed_at: number | null
}

const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL
const baseUrl = (configuredBaseUrl || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000')).replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 15000)
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, signal: controller.signal, headers: { Accept: 'application/json', ...init?.headers } })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error(`Backend request timed out at ${baseUrl}`)
    }
    throw new Error(`Backend unavailable at ${baseUrl}. Start FastAPI with: python -m uvicorn app.main:app --reload`)
  } finally {
    window.clearTimeout(timeout)
  }
  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw new Error(detail?.detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const materialsApi = {
  overview: () => request<Overview>('/api/materials/overview'),
  health: () => request<{ status: string; service: string }>('/api/materials/health'),
  reviews: (search = '', status = 'PENDING') => request<{ items: Review[]; total: number }>(`/api/materials/reviews?${new URLSearchParams({ search, status, page_size: '50' })}`),
  decide: (id: string, action: 'APPROVE' | 'REJECT') => request<Review>(`/api/materials/reviews/${encodeURIComponent(id)}/decision`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action, reviewer: 'Admin' }),
  }),
  canonicals: (search = '', cpse = '', category = '', page = 1, pageSize = 50) =>
    request<CanonicalsResponse>(`/api/materials/canonicals?${new URLSearchParams({
      search, cpse, category, page: String(page), page_size: String(pageSize),
    })}`),
  mappings: () => request<{ items: Mapping[] }>('/api/materials/mappings'),
  startBenchmark: (size = 2000) => request<BenchmarkJob>('/api/materials/benchmark/start', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ size }),
  }),
  benchmarkStatus: (jobId: string) => request<BenchmarkJob>(`/api/materials/benchmark/${encodeURIComponent(jobId)}`),
  benchmarkLatest: () => request<BenchmarkJob>('/api/materials/benchmark/latest'),
  demo: () => request<Record<string, unknown>>('/api/materials/demo'),
  upload: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return request<{ filename: string; validation: { rows: number; columns: string[]; missing_descriptions: number; duplicate_rows: number; valid: boolean }; statistics: Statistics; decision_counts: Record<string, number> }>('/api/materials/upload', { method: 'POST', body })
  },
}
