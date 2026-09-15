/**
 * Centralized CPSE (Central Public Sector Enterprise) metadata configuration.
 * Every page uses this single source for CPSE display names, short codes,
 * brand colors, and full organization names.
 */

export interface CPSEInfo {
  name: string
  shortCode: string
  fullName: string
  color: string
  initials: string
}

/** Master CPSE configuration keyed by canonical name. */
export const CPSE_CONFIG: Record<string, CPSEInfo> = {
  'NTPC': {
    name: 'NTPC',
    shortCode: 'NTPC',
    fullName: 'National Thermal Power Corporation',
    color: '#1a3c72',
    initials: 'NT',
  },
  'BHEL': {
    name: 'BHEL',
    shortCode: 'BHEL',
    fullName: 'Bharat Heavy Electricals Limited',
    color: '#0d47a1',
    initials: 'BH',
  },
  'IOCL': {
    name: 'IOCL',
    shortCode: 'IOCL',
    fullName: 'Indian Oil Corporation Limited',
    color: '#c62828',
    initials: 'IO',
  },
  'ONGC': {
    name: 'ONGC',
    shortCode: 'ONGC',
    fullName: 'Oil and Natural Gas Corporation',
    color: '#1565c0',
    initials: 'ON',
  },
  'GAIL': {
    name: 'GAIL',
    shortCode: 'GAIL',
    fullName: 'GAIL (India) Limited',
    color: '#2e7d32',
    initials: 'GA',
  },
  'SAIL': {
    name: 'SAIL',
    shortCode: 'SAIL',
    fullName: 'Steel Authority of India Limited',
    color: '#283593',
    initials: 'SA',
  },
  'Coal India': {
    name: 'Coal India',
    shortCode: 'CIL',
    fullName: 'Coal India Limited',
    color: '#37474f',
    initials: 'CI',
  },
  'Power Grid': {
    name: 'Power Grid',
    shortCode: 'PGCIL',
    fullName: 'Power Grid Corporation of India',
    color: '#4527a0',
    initials: 'PG',
  },
  'BPCL': {
    name: 'BPCL',
    shortCode: 'BPCL',
    fullName: 'Bharat Petroleum Corporation Limited',
    color: '#e65100',
    initials: 'BP',
  },
  'HPCL': {
    name: 'HPCL',
    shortCode: 'HPCL',
    fullName: 'Hindustan Petroleum Corporation Limited',
    color: '#00695c',
    initials: 'HP',
  },
}

/** Ordered list of all known CPSE names. */
export const CPSE_LIST = Object.keys(CPSE_CONFIG)

/** Resolve CPSE info with a graceful fallback for unknown CPSEs. */
export function getCPSE(name: string): CPSEInfo {
  return CPSE_CONFIG[name] ?? {
    name,
    shortCode: name.substring(0, 4).toUpperCase(),
    fullName: name,
    color: '#718196',
    initials: name.substring(0, 2).toUpperCase(),
  }
}
