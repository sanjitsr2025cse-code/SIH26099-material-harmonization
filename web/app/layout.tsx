import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = { title: 'Bharat Material Grid | SIH Dashboard', description: 'AI-Driven Standardization and Harmonization of Material Codes Across CPSEs — One Nation – One Material Code.' }
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html> }
