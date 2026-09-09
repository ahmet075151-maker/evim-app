"use client"

import { useCallback, useMemo, useRef, useState } from "react"
import { NavContext, type View } from "./nav"
import { useStore } from "@/lib/store"
import { FeedbackProvider, useFeedback } from "./feedback"
import { TopBar } from "./top-bar"
import { HomeScreen } from "./home-screen"
import { NodeScreen } from "./node-screen"
import { ReportScreen } from "./report-screen"
import { TrashScreen } from "./trash-screen"
import { Modal, Button } from "./ui"
import { toCsv, download, timestampName } from "@/lib/export"
import { categoryByKey } from "@/lib/taxonomy"
import type { AppState } from "@/lib/types"

const REPORT_TITLES: Record<string, string> = {
  favorites: "Sık Kullanılanlar",
  shopping: "Alışveriş Listesi",
  forsale: "Satılık Eşyalar",
  donation: "Bağışlıklar",
  lost: "Kayıp Eşyalar",
  moving: "Taşınma Modu",
}

function Shell() {
  const { state, ready, nodeById, importState } = useStore()
  const { toast, confirm } = useFeedback()
  const [stack, setStack] = useState<View[]>([{ name: "home" }])
  const [aboutOpen, setAboutOpen] = useState(false)
  const restoreRef = useRef<HTMLInputElement>(null)

  const view = stack[stack.length - 1]

  const navigate = useCallback((v: View) => setStack((s) => [...s, v]), [])
  const back = useCallback(() => setStack((s) => (s.length > 1 ? s.slice(0, -1) : s)), [])
  const goHome = useCallback(() => setStack([{ name: "home" }]), [])

  const title = useMemo(() => {
    switch (view.name) {
      case "home":
        return "EVİM"
      case "node":
        return nodeById(view.id)?.name ?? "Konum"
      case "category":
        return categoryByKey(view.key)?.label ?? "Kategori"
      case "report":
        return REPORT_TITLES[view.kind] ?? "Rapor"
      case "trash":
        return "Silinenler"
    }
  }, [view, nodeById, state.nodes])

  function onExportCsv() {
    download(timestampName("evim_envanter", "csv"), toCsv(state), "text/csv;charset=utf-8")
    toast("CSV indirildi")
  }

  function onBackup() {
    const backup = JSON.stringify(state, null, 2)
    download(timestampName("evim_yedek", "json"), backup, "application/json")
    toast("Yedek dosyası indirildi")
  }

  async function onRestoreFile(file?: File) {
    if (!file) return
    try {
      const text = await file.text()
      const parsed = JSON.parse(text) as AppState
      if (!parsed || !Array.isArray(parsed.nodes)) throw new Error("bad")
      const ok = await confirm({
        title: "Yedekten geri yükle",
        message: "Mevcut tüm veriler bu yedek dosyasıyla değiştirilecek. Devam edilsin mi?",
        confirmLabel: "Geri Yükle",
        danger: true,
      })
      if (!ok) return
      importState({ nodes: parsed.nodes, trash: parsed.trash ?? [], guestMode: false, version: 1 })
      goHome()
      toast("Envanter geri yüklendi")
    } catch {
      toast("Geçersiz yedek dosyası", "warn")
    }
  }

  if (!ready) {
    return (
      <div className="grid min-h-screen place-items-center">
        <div className="flex flex-col items-center gap-3 text-[var(--color-muted)]">
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-[var(--color-primary)] text-[var(--color-primary-fg)] text-xl font-bold">
            E
          </div>
          <p className="text-sm">Envanter yükleniyor…</p>
        </div>
      </div>
    )
  }

  return (
    <NavContext.Provider value={{ view, navigate, back, canGoBack: stack.length > 1, goHome }}>
      <TopBar title={title} onExportCsv={onExportCsv} onBackup={onBackup} onRestore={() => restoreRef.current?.click()} onAbout={() => setAboutOpen(true)} />
      <main>
        {view.name === "home" && <HomeScreen />}
        {view.name === "node" && <NodeScreen id={view.id} />}
        {view.name === "category" && <ReportScreen categoryKey={view.key} />}
        {view.name === "report" && <ReportScreen kind={view.kind} />}
        {view.name === "trash" && <TrashScreen />}
      </main>

      <input
        ref={restoreRef}
        type="file"
        accept="application/json,.json"
        className="hidden"
        onChange={(e) => onRestoreFile(e.target.files?.[0])}
      />

      <Modal open={aboutOpen} onClose={() => setAboutOpen(false)} title="EVİM Hakkında">
        <div className="space-y-3 text-sm text-[var(--color-muted)]">
          <p>
            <span className="font-semibold text-[var(--color-foreground)]">EVİM</span>, evindeki odaları, kutuları ve eşyaları
            sınırsız bir hiyerarşiyle organize etmeni sağlayan tamamen yerel çalışan bir envanter asistanıdır.
          </p>
          <p>
            Tüm verilerin cihazının tarayıcısında (IndexedDB) güvenle saklanır; hiçbir sunucuya gönderilmez. Verilerini
            kaybetmemek için menüden düzenli olarak <span className="font-medium text-[var(--color-foreground)]">Veritabanı Yedeği</span>{" "}
            alman önerilir.
          </p>
          <ul className="list-inside list-disc space-y-1">
            <li>Sınırsız iç içe kutu/eşya hiyerarşisi</li>
            <li>Fotoğraf, fiyat, stok, SKT/garanti, etiket ve durum bayrakları</li>
            <li>Toplu taşıma/silme, sıralama ve küresel arama</li>
            <li>Silinenler geçmişi ve geri getirme</li>
            <li>CSV dışa aktarma ve tam yedek/geri yükleme</li>
          </ul>
          <p className="text-xs">Sürüm 1.0 · Çevrimdışı çalışır</p>
        </div>
      </Modal>
    </NavContext.Provider>
  )
}

export function EvimApp() {
  return (
    <FeedbackProvider>
      <Shell />
    </FeedbackProvider>
  )
}
