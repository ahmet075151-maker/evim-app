"use client"

import { useMemo, useState } from "react"
import {
  Plus,
  ArrowUpDown,
  CheckSquare,
  Trash2,
  FolderInput,
  Info,
  Pencil,
  ChevronRight,
  Box,
  PackageOpen,
  X,
} from "lucide-react"
import { useStore } from "@/lib/store"
import { useNav } from "./nav"
import { useFeedback } from "./feedback"
import { NodeCard } from "./node-card"
import { ItemEditor } from "./item-editor"
import { Button, EmptyState, IconButton, Modal, Select } from "./ui"
import type { InvNode, NodeType } from "@/lib/types"
import { roomTypeByKey } from "@/lib/taxonomy"
import { formatCurrency } from "@/lib/utils"

type SortKey = "new" | "old" | "az" | "price"

export function NodeScreen({ id }: { id: string }) {
  const { state, nodeById, childrenOf, pathTo, descendants, deleteNodes, moveNodes, updateNode } = useStore()
  const { navigate, goHome } = useNav()
  const { toast, confirm } = useFeedback()

  const node = nodeById(id)
  const [sort, setSort] = useState<SortKey>("new")
  const [selectMode, setSelectMode] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [editorOpen, setEditorOpen] = useState(false)
  const [editorType, setEditorType] = useState<NodeType>("item")
  const [editNode, setEditNode] = useState<InvNode | null>(null)
  const [infoOpen, setInfoOpen] = useState(false)
  const [moveOpen, setMoveOpen] = useState(false)

  const readOnly = state.guestMode

  const children = useMemo(() => {
    const list = [...childrenOf(id)]
    list.sort((a, b) => {
      switch (sort) {
        case "new":
          return b.createdAt - a.createdAt
        case "old":
          return a.createdAt - b.createdAt
        case "az":
          return a.name.localeCompare(b.name, "tr")
        case "price":
          return (b.price ?? 0) - (a.price ?? 0)
      }
    })
    // containers first for clarity
    return list.sort((a, b) => Number(b.type === "container" || b.type === "room") - Number(a.type === "container" || a.type === "room"))
  }, [childrenOf, id, sort, state.nodes])

  if (!node) {
    return (
      <div className="mx-auto max-w-3xl px-3 py-10">
        <EmptyState icon={<PackageOpen className="h-6 w-6" />} title="Bulunamadı" hint="Bu konum silinmiş olabilir." />
        <div className="mt-4 flex justify-center">
          <Button onClick={goHome}>Ana Ekrana Dön</Button>
        </div>
      </div>
    )
  }

  const path = pathTo(id)
  const desc = descendants(id)
  const itemCount = desc.filter((n) => n.type !== "room").length
  const totalValue = desc.reduce((s, n) => s + (n.price ?? 0) * (n.quantity ?? 1), 0)

  function toggleSelect(nid: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(nid) ? next.delete(nid) : next.add(nid)
      return next
    })
  }

  function exitSelect() {
    setSelectMode(false)
    setSelected(new Set())
  }

  async function bulkDelete() {
    const ok = await confirm({
      title: "Seçilenleri sil",
      message: `${selected.size} öğe silinecek. İçerikleriyle birlikte Silinenler'e taşınacak ve geri alınabilir.`,
      confirmLabel: "Sil",
      danger: true,
    })
    if (!ok) return
    deleteNodes([...selected])
    toast(`${selected.size} öğe silindi`)
    exitSelect()
  }

  function doMove(targetId: string | null) {
    moveNodes([...selected], targetId)
    toast(`${selected.size} öğe taşındı`)
    setMoveOpen(false)
    exitSelect()
  }

  function openAdd(type: NodeType) {
    setEditNode(null)
    setEditorType(type)
    setEditorOpen(true)
  }

  function openEdit(n: InvNode) {
    if (readOnly) {
      toast("Misafir modunda düzenleme kapalı", "warn")
      return
    }
    setEditNode(n)
    setEditorType(n.type === "room" ? "item" : n.type)
    setEditorOpen(true)
  }

  const rt = node.type === "room" ? roomTypeByKey(node.roomType) : null

  return (
    <div className="mx-auto max-w-3xl px-3 pb-28 pt-3">
      {/* breadcrumb */}
      <nav className="flex items-center gap-1 overflow-x-auto py-2 text-sm no-scrollbar" aria-label="Gezinti yolu">
        <button onClick={goHome} className="shrink-0 text-[var(--color-muted)] hover:text-[var(--color-foreground)]">
          Ana Ekran
        </button>
        {path.map((p, i) => (
          <span key={p.id} className="flex shrink-0 items-center gap-1">
            <ChevronRight className="h-3.5 w-3.5 text-[var(--color-muted)]" />
            <button
              onClick={() => navigate({ name: "node", id: p.id })}
              className={i === path.length - 1 ? "font-semibold" : "text-[var(--color-muted)] hover:text-[var(--color-foreground)]"}
            >
              {p.name}
            </button>
          </span>
        ))}
      </nav>

      {/* toolbar */}
      <div className="mb-3 flex items-center gap-2">
        <div className="relative">
          <ArrowUpDown className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-muted)]" />
          <Select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="h-10 w-auto py-0 pl-8 pr-8 text-sm"
            aria-label="Sırala"
          >
            <option value="new">Yeniden Eskiye</option>
            <option value="old">Eskiden Yeniye</option>
            <option value="az">A → Z</option>
            <option value="price">Fiyat (Yüksek)</option>
          </Select>
        </div>

        <div className="flex-1" />

        {!readOnly && children.length > 0 && (
          <IconButton label="Toplu Seç" onClick={() => (selectMode ? exitSelect() : setSelectMode(true))}>
            {selectMode ? <X className="h-5 w-5" /> : <CheckSquare className="h-5 w-5" />}
          </IconButton>
        )}
        <IconButton label="Bilgi" onClick={() => setInfoOpen(true)}>
          <Info className="h-5 w-5" />
        </IconButton>
      </div>

      {/* select bar */}
      {selectMode && (
        <div className="mb-3 flex items-center gap-2 rounded-xl border border-[var(--color-primary)] bg-[var(--color-primary)]/10 px-3 py-2 text-sm animate-fade-in">
          <span className="font-medium">{selected.size} seçili</span>
          <div className="flex-1" />
          <Button variant="ghost" className="h-8 px-2" disabled={!selected.size} onClick={() => setMoveOpen(true)}>
            <FolderInput className="h-4 w-4" /> Taşı
          </Button>
          <Button variant="ghost" className="h-8 px-2 text-[var(--color-danger)]" disabled={!selected.size} onClick={bulkDelete}>
            <Trash2 className="h-4 w-4" /> Sil
          </Button>
        </div>
      )}

      {/* list */}
      {children.length === 0 ? (
        <EmptyState
          icon={<PackageOpen className="h-6 w-6" />}
          title="Burası boş"
          hint={readOnly ? "Misafir modunda ekleme kapalı." : "Eşya veya kutu ekleyerek doldurabilirsin."}
        />
      ) : (
        <div className="space-y-2">
          {children.map((c) => (
            <NodeCard
              key={c.id}
              node={c}
              onOpen={(nid) => navigate({ name: "node", id: nid })}
              onEdit={openEdit}
              selectMode={selectMode}
              selected={selected.has(c.id)}
              onToggleSelect={toggleSelect}
            />
          ))}
        </div>
      )}

      {/* FAB */}
      {!readOnly && !selectMode && (
        <div className="fixed inset-x-0 bottom-6 z-30 mx-auto flex max-w-3xl justify-end gap-2 px-4">
          <Button variant="secondary" className="shadow-lg" onClick={() => openAdd("container")}>
            <Box className="h-5 w-5" /> Kutu
          </Button>
          <Button variant="primary" className="shadow-lg" onClick={() => openAdd("item")}>
            <Plus className="h-5 w-5" /> Eşya Ekle
          </Button>
        </div>
      )}

      <ItemEditor
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        parentId={id}
        editNode={editNode}
        defaultType={editorType}
      />

      {/* info / manage */}
      <InfoModal
        open={infoOpen}
        onClose={() => setInfoOpen(false)}
        node={node}
        itemCount={itemCount}
        totalValue={totalValue}
        typeLabel={rt ? rt.label : node.type === "container" ? "Kutu / Dolap" : "Eşya"}
        readOnly={readOnly}
        onRename={(name) => {
          updateNode(node.id, { name })
          toast("İsim güncellendi")
        }}
        onEditItem={() => {
          setInfoOpen(false)
          openEdit(node)
        }}
        onDelete={async () => {
          const ok = await confirm({
            title: `${node.name} silinsin mi?`,
            message: "İçindeki tüm eşyalarla birlikte Silinenler'e taşınacak. Geri alabilirsin.",
            confirmLabel: "Sil",
            danger: true,
          })
          if (!ok) return
          deleteNodes([node.id])
          toast("Silindi")
          setInfoOpen(false)
          node.parentId ? navigate({ name: "node", id: node.parentId }) : goHome()
        }}
      />

      <MovePicker open={moveOpen} onClose={() => setMoveOpen(false)} excludeIds={selected} onPick={doMove} currentParent={id} />
    </div>
  )
}

function InfoModal({
  open,
  onClose,
  node,
  itemCount,
  totalValue,
  typeLabel,
  readOnly,
  onRename,
  onDelete,
  onEditItem,
}: {
  open: boolean
  onClose: () => void
  node: InvNode
  itemCount: number
  totalValue: number
  typeLabel: string
  readOnly: boolean
  onRename: (name: string) => void
  onDelete: () => void
  onEditItem: () => void
}) {
  const [name, setName] = useState(node.name)
  return (
    <Modal open={open} onClose={onClose} title="Bilgi & Yönetim">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-xl bg-[var(--color-surface-2)] p-3">
            <p className="text-xs text-[var(--color-muted)]">Tür</p>
            <p className="font-semibold">{typeLabel}</p>
          </div>
          <div className="rounded-xl bg-[var(--color-surface-2)] p-3">
            <p className="text-xs text-[var(--color-muted)]">Toplam Eşya</p>
            <p className="font-semibold">{itemCount}</p>
          </div>
          <div className="col-span-2 rounded-xl bg-[var(--color-surface-2)] p-3">
            <p className="text-xs text-[var(--color-muted)]">Toplam Değer</p>
            <p className="font-semibold">{formatCurrency(totalValue)}</p>
          </div>
        </div>

        {!readOnly && (
          <>
            <label className="block space-y-1.5">
              <span className="text-xs font-medium text-[var(--color-muted)]">İsmi Değiştir</span>
              <div className="flex gap-2">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
                />
                <Button variant="primary" onClick={() => name.trim() && onRename(name.trim())}>
                  Kaydet
                </Button>
              </div>
            </label>

            {node.type !== "room" && (
              <Button variant="outline" className="w-full" onClick={onEditItem}>
                <Pencil className="h-4 w-4" /> Tüm Detayları Düzenle
              </Button>
            )}

            <Button variant="danger" className="w-full" onClick={onDelete}>
              <Trash2 className="h-4 w-4" /> {node.type === "room" ? "Odayı Sil" : "Sil"}
            </Button>
          </>
        )}
      </div>
    </Modal>
  )
}

function MovePicker({
  open,
  onClose,
  excludeIds,
  onPick,
  currentParent,
}: {
  open: boolean
  onClose: () => void
  excludeIds: Set<string>
  onPick: (targetId: string | null) => void
  currentParent: string
}) {
  const { state, childrenOf, pathTo, descendants } = useStore()

  // valid targets: rooms and containers, not inside the moved subtree, not the current parent
  const blocked = new Set<string>()
  excludeIds.forEach((id) => {
    blocked.add(id)
    descendants(id).forEach((d) => blocked.add(d.id))
  })

  const targets = state.nodes.filter(
    (n) => (n.type === "room" || n.type === "container") && !blocked.has(n.id) && n.id !== currentParent,
  )

  return (
    <Modal open={open} onClose={onClose} title="Nereye taşınsın?">
      <div className="space-y-1.5">
        {targets.length === 0 ? (
          <EmptyState icon={<FolderInput className="h-6 w-6" />} title="Uygun hedef yok" />
        ) : (
          targets.map((t) => {
            const p = pathTo(t.id)
              .map((x) => x.name)
              .join(" › ")
            return (
              <button
                key={t.id}
                onClick={() => onPick(t.id)}
                className="flex w-full items-center gap-2 rounded-xl border border-[var(--color-border)] p-3 text-left text-sm hover:border-[var(--color-muted)]"
              >
                {t.type === "room" ? <PackageOpen className="h-4 w-4 text-[var(--color-muted)]" /> : <Box className="h-4 w-4 text-[var(--color-muted)]" />}
                <span className="truncate">{p}</span>
              </button>
            )
          })
        )}
      </div>
    </Modal>
  )
}
