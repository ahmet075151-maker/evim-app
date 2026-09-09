"use client"

import { useMemo, useState } from "react"
import { Search, Plus, Home as HomeIcon, Package, Boxes, Wallet, CornerDownRight, X } from "lucide-react"
import { useStore } from "@/lib/store"
import { useNav } from "./nav"
import { useFeedback } from "./feedback"
import { Button, EmptyState, Input, Modal } from "./ui"
import { DynIcon } from "./icon"
import { CATEGORIES, roomTypeByKey, guessRoomType } from "@/lib/taxonomy"
import { formatCurrency } from "@/lib/utils"
import type { InvNode } from "@/lib/types"

export function HomeScreen() {
  const { state, childrenOf, addRoom, descendants, pathTo, nodeById } = useStore()
  const { navigate } = useNav()
  const { toast } = useFeedback()
  const [query, setQuery] = useState("")
  const [addOpen, setAddOpen] = useState(false)
  const [roomName, setRoomName] = useState("")

  const rooms = childrenOf(null).filter((n) => n.type === "room")
  const readOnly = state.guestMode

  const stats = useMemo(() => {
    const items = state.nodes.filter((n) => n.type !== "room")
    const total = items.reduce((s, n) => s + (n.price ?? 0) * (n.quantity ?? 1), 0)
    return { itemCount: items.length, roomCount: rooms.length, total }
  }, [state.nodes, rooms.length])

  const results = useMemo(() => {
    const q = query.trim().toLocaleLowerCase("tr")
    if (!q) return []
    return state.nodes
      .filter((n) => n.type !== "room")
      .filter(
        (n) =>
          n.name.toLocaleLowerCase("tr").includes(q) ||
          n.code?.toLowerCase().includes(q.toLowerCase()) ||
          (n.tags ?? []).some((t) => t.toLocaleLowerCase("tr").includes(q)),
      )
      .slice(0, 40)
  }, [query, state.nodes])

  function openResult(n: InvNode) {
    if (n.type === "container") navigate({ name: "node", id: n.id })
    else if (n.parentId) navigate({ name: "node", id: n.parentId })
  }

  function createRoom() {
    if (!roomName.trim()) return
    const r = addRoom(roomName)
    setRoomName("")
    setAddOpen(false)
    toast(`${r.name} eklendi`)
    navigate({ name: "node", id: r.id })
  }

  function roomStats(id: string) {
    const desc = descendants(id)
    const count = desc.filter((n) => n.type !== "room").length
    const value = desc.reduce((s, n) => s + (n.price ?? 0) * (n.quantity ?? 1), 0)
    return { count, value }
  }

  return (
    <div className="mx-auto max-w-3xl px-3 pb-28 pt-4">
      {/* search */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[var(--color-muted)]" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Tüm eşyalarda ara (isim, kod, etiket)…"
          className="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] py-3.5 pl-12 pr-11 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            aria-label="Temizle"
            className="absolute right-3 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center rounded-lg text-[var(--color-muted)] hover:bg-[var(--color-surface-2)]"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {query ? (
        <div className="mt-4 space-y-2 animate-fade-in">
          <p className="px-1 text-xs text-[var(--color-muted)]">{results.length} sonuç bulundu</p>
          {results.length === 0 ? (
            <EmptyState icon={<Search className="h-6 w-6" />} title="Sonuç yok" hint="Farklı bir kelime deneyin." />
          ) : (
            results.map((n) => {
              const path = pathTo(n.id)
                .slice(0, -1)
                .map((p) => p.name)
                .join(" › ")
              return (
                <button
                  key={n.id}
                  onClick={() => openResult(n)}
                  className="flex w-full items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-left hover:border-[var(--color-muted)]"
                >
                  <div className="grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-lg bg-[var(--color-surface-2)]">
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
                  {n.code && <span className="shrink-0 font-mono text-[11px] text-[var(--color-muted)]">{n.code}</span>}
                </button>
              )
            })
          )}
        </div>
      ) : (
        <>
          {/* stats */}
          <div className="mt-4 grid grid-cols-3 gap-2">
            <StatCard icon={<HomeIcon className="h-4 w-4" />} label="Oda" value={String(stats.roomCount)} />
            <StatCard icon={<Package className="h-4 w-4" />} label="Eşya" value={String(stats.itemCount)} />
            <StatCard icon={<Wallet className="h-4 w-4" />} label="Değer" value={formatCurrency(stats.total)} />
          </div>

          {/* categories */}
          <section className="mt-6">
            <h2 className="mb-2 px-1 text-sm font-semibold text-[var(--color-muted)]">Kategoriler</h2>
            <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
              {CATEGORIES.map((c) => (
                <button
                  key={c.key}
                  onClick={() => navigate({ name: "category", key: c.key })}
                  className="flex shrink-0 items-center gap-2 rounded-full border border-[var(--color-border)] px-3.5 py-2 text-sm font-medium hover:border-[var(--color-muted)]"
                  style={{ backgroundColor: `${c.color}18`, color: c.color }}
                >
                  <DynIcon name={c.icon} className="h-4 w-4" />
                  {c.label}
                </button>
              ))}
            </div>
          </section>

          {/* rooms */}
          <section className="mt-6">
            <div className="mb-2 flex items-center justify-between px-1">
              <h2 className="text-sm font-semibold text-[var(--color-muted)]">Odalar</h2>
              {!readOnly && (
                <Button variant="ghost" className="h-8 px-2 text-sm" onClick={() => setAddOpen(true)}>
                  <Plus className="h-4 w-4" /> Oda Ekle
                </Button>
              )}
            </div>

            {rooms.length === 0 ? (
              <EmptyState
                icon={<HomeIcon className="h-6 w-6" />}
                title="Henüz oda yok"
                hint={readOnly ? "Misafir modunda düzenleme kapalı." : "İlk odanı ekleyerek envanterini oluşturmaya başla."}
              />
            ) : (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {rooms.map((room) => {
                  const rt = roomTypeByKey(room.roomType)
                  const s = roomStats(room.id)
                  return (
                    <button
                      key={room.id}
                      onClick={() => navigate({ name: "node", id: room.id })}
                      className="group flex flex-col gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-left transition-colors hover:border-[var(--color-muted)]"
                    >
                      <div
                        className="grid h-12 w-12 place-items-center rounded-xl"
                        style={{ backgroundColor: `${room.color ?? rt.color}22`, color: room.color ?? rt.color }}
                      >
                        <DynIcon name={rt.icon} className="h-6 w-6" />
                      </div>
                      <div>
                        <p className="truncate font-semibold">{room.name}</p>
                        <p className="text-xs text-[var(--color-muted)]">{rt.label}</p>
                      </div>
                      <div className="flex items-center justify-between text-xs text-[var(--color-muted)]">
                        <span>{s.count} eşya</span>
                        <span className="font-medium">{formatCurrency(s.value)}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </section>
        </>
      )}

      <Modal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        title="Yeni Oda"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAddOpen(false)}>
              Vazgeç
            </Button>
            <Button variant="primary" onClick={createRoom}>
              Ekle
            </Button>
          </div>
        }
      >
        <div className="space-y-3">
          <Input
            autoFocus
            value={roomName}
            onChange={(e) => setRoomName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.nativeEvent.isComposing) createRoom()
            }}
            placeholder="Örn: Yatak Odası"
          />
          {roomName.trim() && (
            <div className="flex items-center gap-2 rounded-xl bg-[var(--color-surface-2)] p-3 text-sm">
              <DynIcon name={guessRoomType(roomName).icon} className="h-5 w-5" />
              <span className="text-[var(--color-muted)]">Tahmini tür:</span>
              <span className="font-medium">{guessRoomType(roomName).label}</span>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
      <div className="flex items-center gap-1.5 text-[var(--color-muted)]">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className="mt-1 truncate text-lg font-bold">{value}</p>
    </div>
  )
}
