import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function uid() {
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4)
}

export function formatCurrency(v?: number) {
  if (v == null || isNaN(v)) return "—"
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    maximumFractionDigits: 0,
  }).format(v)
}

// parse GG/AA/YYYY or ISO -> Date
export function parseDate(s?: string | null): Date | null {
  if (!s) return null
  const tr = s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
  if (tr) {
    const [, d, m, y] = tr
    return new Date(Number(y), Number(m) - 1, Number(d))
  }
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

export function daysUntil(s?: string | null): number | null {
  const d = parseDate(s)
  if (!d) return null
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  d.setHours(0, 0, 0, 0)
  return Math.round((d.getTime() - now.getTime()) / 86400000)
}

export function formatDateTr(d: Date) {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(d)
}
