"use client"

import { RotateCcw, Trash2, History, Home, Box, Package } from "lucide-react"
import { useStore } from "@/lib/store"
import { useFeedback } from "./feedback"
import { Button, EmptyState } from "./ui"
import { formatDateTr } from "@/lib/utils"

export function TrashScreen() {
  const { state, restoreTrash, clearTrash } = useStore()
  const { toast, confirm } = useFeedback()

  async function onClear() {
    const ok = await confirm({
      title: "Geçmişi temizle",
      message: "Silinenler geçmişi kalıcı olarak temizlenecek. Bu işlem geri alınamaz.",
      confirmLabel: "Temizle",
      danger: true,
    })
    if (!ok) return
    clearTrash()
    toast("Geçmiş temizlendi")
  }

  return (
    <div className="mx-auto max-w-3xl px-3 pb-28 pt-4">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-[var(--color-muted)]">{state.trash.length} silinmiş kayıt</p>
        {state.trash.length > 0 && (
          <Button variant="ghost" className="h-8 px-2 text-[var(--color-danger)]" onClick={onClear}>
            <Trash2 className="h-4 w-4" /> Geçmişi Temizle
          </Button>
        )}
      </div>

      {state.trash.length === 0 ? (
        <EmptyState icon={<History className="h-6 w-6" />} title="Geçmiş boş" hint="Sildiğin oda ve eşyalar burada birikir; tek tuşla geri getirebilirsin." />
      ) : (
        <div className="space-y-2">
          {state.trash.map((entry) => {
            const childCount = entry.nodes.length - 1
            return (
              <div
                key={entry.id}
                className="flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3"
              >
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-[var(--color-surface-2)] text-[var(--color-muted)]">
                  {entry.rootType === "room" ? <Home className="h-5 w-5" /> : entry.rootType === "container" ? <Box className="h-5 w-5" /> : <Package className="h-5 w-5" />}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{entry.rootName}</p>
                  <p className="text-xs text-[var(--color-muted)]">
                    {formatDateTr(new Date(entry.deletedAt))}
                    {childCount > 0 ? ` · ${childCount} alt öğe` : ""}
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={() => {
                    restoreTrash(entry.id)
                    toast(`${entry.rootName} geri getirildi`)
                  }}
                >
                  <RotateCcw className="h-4 w-4" /> Geri Getir
                </Button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
