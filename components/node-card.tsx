"use client"

import { useState } from "react"
import {
  Box,
  ChevronDown,
  ChevronRight,
  Star,
  HandCoins,
  Gift,
  MapPinOff,
  Clock,
  ShieldCheck,
  HandHelping,
  PackageOpen,
  Truck,
  Check,
} from "lucide-react"
import type { InvNode } from "@/lib/types"
import { useStore } from "@/lib/store"
import { Badge } from "./ui"
import { DynIcon } from "./icon"
import { categoryByKey } from "@/lib/taxonomy"
import { cn, daysUntil, formatCurrency } from "@/lib/utils"

interface Props {
  node: InvNode
  onOpen: (id: string) => void
  onEdit: (node: InvNode) => void
  selectMode?: boolean
  selected?: boolean
  onToggleSelect?: (id: string) => void
  depth?: number
}

function DateBadge({ label, date, kind }: { label: string; date?: string | null; kind: "expiry" | "warranty" }) {
  const d = daysUntil(date)
  if (d == null) return null
  const Icon = kind === "expiry" ? Clock : ShieldCheck
  if (d < 0) {
    return (
      <Badge color="#ef4444">
        <Icon className="h-3 w-3" /> {kind === "expiry" ? "Süresi Doldu" : "Garanti Bitti"}
      </Badge>
    )
  }
  const color = d <= 7 ? "#f59e0b" : d <= 30 ? "#eab308" : "#22c55e"
  return (
    <Badge color={color}>
      <Icon className="h-3 w-3" /> {d}g kaldı
    </Badge>
  )
}

export function NodeCard({ node, onOpen, onEdit, selectMode, selected, onToggleSelect, depth = 0 }: Props) {
  const { childrenOf } = useStore()
  const [expanded, setExpanded] = useState(false)
  const isContainer = node.type === "container" || node.type === "room"
  const children = isContainer ? childrenOf(node.id) : []
  const cat = categoryByKey(node.category)
  const lowStock = node.minStock != null && (node.quantity ?? 0) <= node.minStock

  function handleClick() {
    if (selectMode) {
      onToggleSelect?.(node.id)
      return
    }
    if (isContainer) onOpen(node.id)
    else onEdit(node)
  }

  return (
    <div>
      <div
        className={cn(
          "group flex items-stretch gap-3 rounded-2xl border bg-[var(--color-surface)] p-3 transition-colors",
          selected ? "border-[var(--color-primary)] ring-1 ring-[var(--color-primary)]" : "border-[var(--color-border)] hover:border-[var(--color-muted)]",
        )}
      >
        {selectMode && (
          <button
            onClick={() => onToggleSelect?.(node.id)}
            aria-label="Seç"
            className={cn(
              "mt-0.5 grid h-6 w-6 shrink-0 place-items-center self-center rounded-md border",
              selected ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white" : "border-[var(--color-border)]",
            )}
          >
            {selected && <Check className="h-4 w-4" />}
          </button>
        )}

        <button onClick={handleClick} className="flex min-w-0 flex-1 items-center gap-3 text-left">
          <div
            className="grid h-12 w-12 shrink-0 place-items-center overflow-hidden rounded-xl"
            style={{ backgroundColor: `${(cat?.color ?? node.color ?? "#6366f1")}22` }}
          >
            {node.photo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={node.photo || "/placeholder.svg"} alt="" className="h-full w-full object-cover" />
            ) : node.type === "container" ? (
              <Box className="h-6 w-6" style={{ color: node.color ?? cat?.color ?? "#6366f1" }} />
            ) : isContainer ? (
              <DynIcon name={undefined} className="h-6 w-6" />
            ) : (
              <DynIcon name={cat?.icon} className="h-6 w-6" style={{ color: cat?.color }} />
            )}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate font-medium">{node.name}</span>
              {node.favorite && <Star className="h-3.5 w-3.5 shrink-0 fill-[#f59e0b] text-[#f59e0b]" />}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-1.5">
              {node.code && <span className="text-[11px] font-mono text-[var(--color-muted)]">{node.code}</span>}
              {cat && <Badge color={cat.color}>{cat.label}</Badge>}
              {node.price != null && <Badge>{formatCurrency(node.price)}</Badge>}
              {node.type !== "container" && node.quantity != null && (
                <Badge color={lowStock ? "#ef4444" : undefined}>
                  {node.quantity} {node.unit}
                </Badge>
              )}
              <DateBadge kind="expiry" date={node.expiryDate} label="SKT" />
              <DateBadge kind="warranty" date={node.warrantyDate} label="Garanti" />
              {node.borrowedTo && (
                <Badge color="#8b5cf6">
                  <HandHelping className="h-3 w-3" /> {node.borrowedTo}
                </Badge>
              )}
              {node.forSale && (
                <Badge color="#22c55e">
                  <HandCoins className="h-3 w-3" /> Satılık
                </Badge>
              )}
              {node.donation && (
                <Badge color="#8b5cf6">
                  <Gift className="h-3 w-3" /> Bağış
                </Badge>
              )}
              {node.lost && (
                <Badge color="#ef4444">
                  <MapPinOff className="h-3 w-3" /> Kayıp
                </Badge>
              )}
              {node.boxNo != null && (
                <Badge color="#0ea5e9">
                  <Truck className="h-3 w-3" /> Koli {node.boxNo}
                </Badge>
              )}
            </div>
          </div>
        </button>

        {isContainer && (
          <div className="flex flex-col items-end justify-between gap-1">
            {children.length > 0 ? (
              <button
                onClick={() => setExpanded((v) => !v)}
                aria-label={expanded ? "Daralt" : "Genişlet"}
                className="grid h-8 w-8 place-items-center rounded-lg text-[var(--color-muted)] hover:bg-[var(--color-surface-2)]"
              >
                {expanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
              </button>
            ) : (
              <span className="grid h-8 w-8 place-items-center text-[var(--color-muted)]">
                <PackageOpen className="h-4 w-4 opacity-40" />
              </span>
            )}
            <span className="rounded-full bg-[var(--color-surface-2)] px-2 py-0.5 text-[11px] text-[var(--color-muted)]">
              {children.length} öğe
            </span>
          </div>
        )}
      </div>

      {isContainer && expanded && children.length > 0 && (
        <div className="ml-4 mt-2 space-y-2 border-l border-dashed border-[var(--color-border)] pl-3">
          {children.map((c) => (
            <NodeCard
              key={c.id}
              node={c}
              onOpen={onOpen}
              onEdit={onEdit}
              selectMode={selectMode}
              selected={selected}
              onToggleSelect={onToggleSelect}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
