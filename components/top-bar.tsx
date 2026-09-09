"use client"

import { useEffect, useRef, useState } from "react"
import {
  ChevronLeft,
  Menu as MenuIcon,
  Home,
  Star,
  ShoppingCart,
  HandCoins,
  Gift,
  MapPinOff,
  Truck,
  Trash2,
  FileDown,
  DatabaseBackup,
  Upload,
  Eye,
  EyeOff,
  ShieldQuestion,
} from "lucide-react"
import { IconButton } from "./ui"
import { useNav } from "./nav"
import { useStore } from "@/lib/store"
import { cn } from "@/lib/utils"

interface Props {
  title: string
  onExportCsv: () => void
  onBackup: () => void
  onRestore: () => void
  onAbout: () => void
}

export function TopBar({ title, onExportCsv, onBackup, onRestore, onAbout }: Props) {
  const { back, canGoBack, navigate, goHome } = useNav()
  const { state, setGuest } = useStore()
  const [open, setOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpen(false)
    }
    window.addEventListener("mousedown", onClick)
    return () => window.removeEventListener("mousedown", onClick)
  }, [open])

  const items: { label: string; icon: typeof Home; action: () => void; tone?: "danger" }[] = [
    { label: "Ana Ekran", icon: Home, action: () => goHome() },
    { label: "Sık Kullanılanlar", icon: Star, action: () => navigate({ name: "report", kind: "favorites" }) },
    { label: "Alışveriş Listesi", icon: ShoppingCart, action: () => navigate({ name: "report", kind: "shopping" }) },
    { label: "Satılık Eşyalar", icon: HandCoins, action: () => navigate({ name: "report", kind: "forsale" }) },
    { label: "Bağışlıklar", icon: Gift, action: () => navigate({ name: "report", kind: "donation" }) },
    { label: "Kayıp Eşyalar", icon: MapPinOff, action: () => navigate({ name: "report", kind: "lost" }) },
    { label: "Taşınma Modu", icon: Truck, action: () => navigate({ name: "report", kind: "moving" }) },
    { label: "Silinenler (Geri Al)", icon: Trash2, action: () => navigate({ name: "trash" }) },
  ]

  const tools: { label: string; icon: typeof Home; action: () => void }[] = [
    { label: "CSV Dışa Aktar", icon: FileDown, action: onExportCsv },
    { label: "Veritabanı Yedeği Al", icon: DatabaseBackup, action: onBackup },
    { label: "Yedekten Geri Yükle", icon: Upload, action: onRestore },
    { label: "Hakkında", icon: ShieldQuestion, action: onAbout },
  ]

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-background)]/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-3xl items-center gap-2 px-3">
        {canGoBack ? (
          <IconButton label="Geri" onClick={back}>
            <ChevronLeft className="h-6 w-6" />
          </IconButton>
        ) : (
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--color-primary)] text-[var(--color-primary-fg)] font-bold">
            E
          </div>
        )}
        <h1 className="min-w-0 flex-1 truncate text-lg font-semibold">{title}</h1>

        {state.guestMode && (
          <span className="hidden items-center gap-1.5 rounded-full bg-[var(--color-warning)]/15 px-3 py-1 text-xs font-semibold text-[var(--color-warning)] sm:inline-flex">
            <Eye className="h-3.5 w-3.5" /> Misafir Modu
          </span>
        )}

        <div className="relative" ref={menuRef}>
          <IconButton label="Menü" onClick={() => setOpen((v) => !v)}>
            <MenuIcon className="h-6 w-6" />
          </IconButton>
          {open && (
            <div className="absolute right-0 top-12 z-50 w-64 overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1.5 shadow-2xl animate-fade-in">
              <button
                onClick={() => {
                  setGuest(!state.guestMode)
                  setOpen(false)
                }}
                className="mb-1 flex w-full items-center gap-3 rounded-xl bg-[var(--color-surface-2)] px-3 py-2.5 text-sm"
              >
                {state.guestMode ? <EyeOff className="h-4 w-4 text-[var(--color-warning)]" /> : <Eye className="h-4 w-4" />}
                <span className="flex-1 text-left">Misafir Modu</span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[11px] font-semibold",
                    state.guestMode ? "bg-[var(--color-warning)] text-black" : "bg-[var(--color-border)] text-[var(--color-muted)]",
                  )}
                >
                  {state.guestMode ? "Açık" : "Kapalı"}
                </span>
              </button>
              {items.map((it) => (
                <MenuRow key={it.label} {...it} close={() => setOpen(false)} />
              ))}
              <div className="my-1 h-px bg-[var(--color-border)]" />
              {tools.map((it) => (
                <MenuRow key={it.label} {...it} close={() => setOpen(false)} />
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

function MenuRow({
  label,
  icon: Icon,
  action,
  close,
}: {
  label: string
  icon: typeof Home
  action: () => void
  close: () => void
}) {
  return (
    <button
      onClick={() => {
        action()
        close()
      }}
      className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm hover:bg-[var(--color-surface-2)]"
    >
      <Icon className="h-4 w-4 text-[var(--color-muted)]" />
      <span className="flex-1 text-left">{label}</span>
    </button>
  )
}
