import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = { title: 'Bharath Mati | One Nation – One Material Code', description: 'Bharath Mati national material registry dashboard for SIH 2024.' }
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html> }
