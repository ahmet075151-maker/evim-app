"use client"

import { useMemo } from "react"
import {
  Star,
  ShoppingCart,
  HandCoins,
  Gift,
  MapPinOff,
  Truck,
  Copy,
  MessageCircle,
  CornerDownRight,
  Package,
  Boxes,
} from "lucide-react"
import { useStore } from "@/lib/store"
import { useNav, type ReportKind } from "./nav"
import { useFeedback } from "./feedback"
import { Badge, Button, EmptyState } from "./ui"
import { categoryByKey } from "@/lib/taxonomy"
import { formatCurrency } from "@/lib/utils"
import type { InvNode } from "@/lib/types"

const META: Record<ReportKind, { title: string; icon: typeof Star; color: string; hint: string }> = {
  favorites: { title: "Sık Kullanılanlar", icon: Star, color: "#f59e0b", hint: "Favori işaretlediğin eşyalar." },
  shopping: { title: "Alışveriş Listesi", icon: ShoppingCart, color: "#ef4444", hint: "Minimum stok sınırının altındaki ürünler." },
  forsale: { title: "Satılık Eşyalar", icon: HandCoins, color: "#22c55e", hint: "Satılık olarak işaretlenenler." },
  donation: { title: "Bağışlıklar", icon: Gift, color: "#8b5cf6", hint: "Bağış olarak işaretlenenler." },
  lost: { title: "Kayıp Eşyalar", icon: MapPinOff, color: "#ef4444", hint: "Kayıp olarak işaretlenenler." },
  moving: { title: "Taşınma Modu", icon: Truck, color: "#0ea5e9", hint: "Koli numarası atanmış eşyalar." },
}

export function ReportScreen({ kind, categoryKey }: { kind?: ReportKind; categoryKey?: string }) {
  const { state, pathTo } = useStore()
  const { navigate } = useNav()
  const { toast } = useFeedback()

  const cat = categoryKey ? categoryByKey(categoryKey) : undefined
  const meta = kind ? META[kind] : undefined

  const results = useMemo(() => {
    const items = state.nodes.filter((n) => n.type !== "room")
    let list: InvNode[] = []
    if (categoryKey) {
      list = items.filter((n) => n.category === categoryKey)
    } else if (kind === "favorites") list = items.filter((n) => n.favorite)
    else if (kind === "shopping") list = items.filter((n) => n.minStock != null && (n.quantity ?? 0) <= n.minStock!)
    else if (kind === "forsale") list = items.filter((n) => n.forSale)
    else if (kind === "donation") list = items.filter((n) => n.donation)
    else if (kind === "lost") list = items.filter((n) => n.lost)
    else if (kind === "moving") list = items.filter((n) => n.boxNo != null)

    if (kind === "moving") list = [...list].sort((a, b) => (a.boxNo ?? 0) - (b.boxNo ?? 0))
    else list = [...list].sort((a, b) => a.name.localeCompare(b.name, "tr"))
    return list
  }, [state.nodes, kind, categoryKey])

  function open(n: InvNode) {
    if (n.type === "container") navigate({ name: "node", id: n.id })
    else if (n.parentId) navigate({ name: "node", id: n.parentId })
  }

  function shoppingText() {
    return (
      "🛒 Alışveriş Listesi\n" +
      results
        .map((n) => `• ${n.name}${n.minStock != null ? ` (kalan: ${n.quantity ?? 0} ${n.unit})` : ""}`)
        .join("\n")
    )
  }

  async function copyList() {
    try {
      await navigator.clipboard.writeText(shoppingText())
      toast("Liste panoya kopyalandı")
    } catch {
      toast("Kopyalanamadı", "warn")
    }
  }

  function sendWhatsapp() {
    const url = `https://wa.me/?text=${encodeURIComponent(shoppingText())}`
    window.open(url, "_blank")
  }

  const title = cat ? cat.label : meta?.title ?? "Rapor"
  const color = cat?.color ?? meta?.color ?? "#6366f1"
  const totalValue = results.reduce((s, n) => s + (n.price ?? 0) * (n.quantity ?? 1), 0)

  return (
    <div className="mx-auto max-w-3xl px-3 pb-28 pt-4">
      <div className="mb-4 flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <div>
          <p className="text-sm text-[var(--color-muted)]">{cat ? "Kategori" : meta?.hint}</p>
          <p className="text-lg font-bold" style={{ color }}>
            {title}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-[var(--color-muted)]">{results.length} eşya</p>
          <p className="font-semibold">{formatCurrency(totalValue)}</p>
        </div>
      </div>

      {kind === "shopping" && results.length > 0 && (
        <div className="mb-4 flex gap-2">
          <Button variant="outline" className="flex-1" onClick={copyList}>
            <Copy className="h-4 w-4" /> Panoya Kopyala
          </Button>
          <Button variant="primary" className="flex-1" onClick={sendWhatsapp}>
            <MessageCircle className="h-4 w-4" /> WhatsApp
          </Button>
        </div>
      )}

      {results.length === 0 ? (
        <EmptyState icon={<Package className="h-6 w-6" />} title="Liste boş" hint={cat ? "Bu kategoride eşya yok." : meta?.hint} />
      ) : (
        <div className="space-y-2">
          {results.map((n) => {
            const c = categoryByKey(n.category)
            const path = pathTo(n.id)
              .slice(0, -1)
              .map((p) => p.name)
              .join(" › ")
            return (
              <button
                key={n.id}
                onClick={() => open(n)}
                className="flex w-full items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-left hover:border-[var(--color-muted)]"
              >
                <div className="grid h-11 w-11 shrink-0 place-items-center overflow-hidden rounded-lg bg-[var(--color-surface-2)]">
                  {n.photo ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={n.photo || "/placeholder.svg"} alt="" className="h-full w-full object-cover" />
                  ) : n.type === "container" ? (
                    <Boxes className="h-5 w-5 text-[var(--color-muted)]" />
                  ) : (
                    <Package className="h-5 w-5 text-[var(--color-muted)]" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{n.name}</p>
                  <p className="flex items-center gap-1 truncate text-xs text-[var(--color-muted)]">
                    <CornerDownRight className="h-3 w-3 shrink-0" /> {path || "—"}
                  </p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  {kind === "moving" && n.boxNo != null && <Badge color="#0ea5e9">Koli {n.boxNo}</Badge>}
                  {kind === "shopping" && (
                    <Badge color="#ef4444">
                      {n.quantity ?? 0}/{n.minStock} {n.unit}
                    </Badge>
                  )}
                  {c && <Badge color={c.color}>{c.label}</Badge>}
                </div>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
