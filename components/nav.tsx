"use client"

import { createContext, useContext } from "react"

export type ReportKind = "favorites" | "shopping" | "forsale" | "donation" | "lost" | "moving"

export type View =
  | { name: "home" }
  | { name: "node"; id: string }
  | { name: "category"; key: string }
  | { name: "report"; kind: ReportKind }
  | { name: "trash" }

interface NavCtx {
  view: View
  navigate: (v: View) => void
  back: () => void
  canGoBack: boolean
  goHome: () => void
}

export const NavContext = createContext<NavCtx | null>(null)

export function useNav() {
  const ctx = useContext(NavContext)
  if (!ctx) throw new Error("useNav must be used within NavContext")
  return ctx
}
