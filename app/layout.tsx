import type { Metadata, Viewport } from "next"
import { GeistSans } from "geist/font/sans"
import "./globals.css"
import { StoreProvider } from "@/lib/store"

export const metadata: Metadata = {
  title: "EVİM — Ev Eşya Envanteri",
  description:
    "Evindeki odaları, kutuları ve eşyaları sınırsız hiyerarşiyle organize et. Tamamen yerel, çevrimdışı çalışan envanter asistanı.",
  generator: "v0.app",
}

export const viewport: Viewport = {
  themeColor: "#0c0d12",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" className={`dark ${GeistSans.variable}`}>
      <body>
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  )
}
