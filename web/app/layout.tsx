import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = { title: 'Material Harmonization Control Center', description: 'SIH governed material harmonization and canonical registry dashboard' }
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html> }
