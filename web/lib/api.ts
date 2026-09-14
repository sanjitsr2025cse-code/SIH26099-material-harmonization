export type Statistics = {
  records: number
  canonical_materials: number
  mappings: number
  mapping_history: number
  pending_reviews: number
}

export type Overview = {
  statistics: Statistics
  decision_counts: Record<string, number>
  review_metrics: Record<string, number>
  health: string
}

export type Review = {
  review_id: string
  left_id: string
  right_id: string
  status: string
  ai_decision: { confidence: number; decision: string; explanation: string[] }
}

export type Canonical = {
  cnmc_id: string
  record: Record<string, unknown>
  member_ids: string[]
  source_records: Record<string, unknown>[]
  metadata: { member_count: number; source_systems: string[]; source_codes: string[]; [key: string]: unknown }
  status: string
  version: number
}

export type Mapping = {
  source_code: string
  source_system: string
  cnmc_id: string
  material_record_id: string
  event_type: string
  sequence: number
  source_description: string
  metadata: Record<string, unknown>
}

const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, headers: { Accept: 'application/json', ...init?.headers } })
  } catch {
    throw new Error(`Backend unavailable at ${baseUrl}. Start FastAPI with: python -m uvicorn app.main:app --reload`)
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
  canonicals: (search = '') => request<{ items: Canonical[] }>(`/api/materials/canonicals?${new URLSearchParams({ search })}`),
  mappings: () => request<{ items: Mapping[] }>('/api/materials/mappings'),
  benchmark: () => request<Record<string, unknown>>('/api/materials/benchmark'),
  demo: () => request<Record<string, unknown>>('/api/materials/demo'),
  upload: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return request<{ filename: string; validation: { rows: number; columns: string[]; missing_descriptions: number; duplicate_rows: number; issues: Array<{ code: string; message: string; count?: number }>; valid: boolean }; statistics: Statistics; decision_counts: Record<string, number> }>('/api/materials/upload', { method: 'POST', body })
  },
}
