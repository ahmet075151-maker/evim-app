"use client"

import { useEffect, useRef, useState } from "react"
import { Camera, ImageIcon, Trash2, Box, PackageOpen, Star, Tag, HandCoins, Gift, MapPinOff } from "lucide-react"
import { Button, Field, Input, Modal, Select, Textarea } from "./ui"
import { CATEGORIES, UNITS } from "@/lib/taxonomy"
import { useStore } from "@/lib/store"
import { processImageFile } from "@/lib/image"
import type { InvNode, NodeType, Unit } from "@/lib/types"
import { cn } from "@/lib/utils"
import { useFeedback } from "./feedback"

interface Props {
  open: boolean
  onClose: () => void
  parentId: string | null
  editNode?: InvNode | null
  defaultType?: NodeType
}

const empty = {
  name: "",
  type: "item" as NodeType,
  category: "",
  price: "",
  quantity: "1",
  unit: "Adet" as Unit,
  minStock: "",
  expiryDate: "",
  warrantyDate: "",
  borrowedTo: "",
  tags: "",
  boxNo: "",
  favorite: false,
  forSale: false,
  donation: false,
  lost: false,
  photo: null as string | null,
}

export function ItemEditor({ open, onClose, parentId, editNode, defaultType = "item" }: Props) {
  const { addNode, updateNode } = useStore()
  const { toast } = useFeedback()
  const [form, setForm] = useState(empty)
  const [busy, setBusy] = useState(false)
  const galleryRef = useRef<HTMLInputElement>(null)
  const cameraRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open) return
    if (editNode) {
      setForm({
        name: editNode.name,
        type: editNode.type === "room" ? "item" : editNode.type,
        category: editNode.category ?? "",
        price: editNode.price != null ? String(editNode.price) : "",
        quantity: editNode.quantity != null ? String(editNode.quantity) : "1",
        unit: editNode.unit ?? "Adet",
        minStock: editNode.minStock != null ? String(editNode.minStock) : "",
        expiryDate: editNode.expiryDate ?? "",
        warrantyDate: editNode.warrantyDate ?? "",
        borrowedTo: editNode.borrowedTo ?? "",
        tags: (editNode.tags ?? []).join(", "),
        boxNo: editNode.boxNo != null ? String(editNode.boxNo) : "",
        favorite: !!editNode.favorite,
        forSale: !!editNode.forSale,
        donation: !!editNode.donation,
        lost: !!editNode.lost,
        photo: editNode.photo ?? null,
      })
    } else {
      setForm({ ...empty, type: defaultType })
    }
  }, [open, editNode, defaultType])

  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) => setForm((f) => ({ ...f, [k]: v }))

  async function onPickFile(file?: File) {
    if (!file) return
    setBusy(true)
    try {
      const data = await processImageFile(file)
      set("photo", data)
    } catch {
      toast("Fotoğraf işlenemedi", "warn")
    } finally {
      setBusy(false)
    }
  }

  function save() {
    if (!form.name.trim()) {
      toast("Lütfen bir isim girin", "warn")
      return
    }
    const patch = {
      name: form.name.trim(),
      type: form.type,
      category: form.category || undefined,
      price: form.price ? Number(form.price) : undefined,
      quantity: form.quantity ? Number(form.quantity) : 1,
      unit: form.unit,
      minStock: form.minStock ? Number(form.minStock) : undefined,
      expiryDate: form.expiryDate || null,
      warrantyDate: form.warrantyDate || null,
      borrowedTo: form.borrowedTo.trim() || undefined,
      tags: form.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
      boxNo: form.boxNo ? Number(form.boxNo) : null,
      favorite: form.favorite,
      forSale: form.forSale,
      donation: form.donation,
      lost: form.lost,
      photo: form.photo,
    }
    if (editNode) {
      updateNode(editNode.id, patch)
      toast("Değişiklikler kaydedildi")
    } else {
      addNode({ ...patch, parentId })
      toast(form.type === "container" ? "Kutu eklendi" : "Eşya eklendi")
    }
    onClose()
  }

  const flags: { key: "favorite" | "forSale" | "donation" | "lost"; label: string; icon: typeof Star; color: string }[] = [
    { key: "favorite", label: "Favori", icon: Star, color: "#f59e0b" },
    { key: "forSale", label: "Satılık", icon: HandCoins, color: "#22c55e" },
    { key: "donation", label: "Bağış", icon: Gift, color: "#8b5cf6" },
    { key: "lost", label: "Kayıp", icon: MapPinOff, color: "#ef4444" },
  ]

  return (
    <Modal
      open={open}
      onClose={onClose}
      wide
      title={editNode ? "Düzenle" : form.type === "container" ? "Yeni Kutu / Dolap" : "Yeni Eşya"}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Vazgeç
          </Button>
          <Button variant="primary" onClick={save}>
            Kaydet
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* type switch */}
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => set("type", "item")}
            className={cn(
              "flex items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-medium",
              form.type === "item"
                ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                : "border-[var(--color-border)] text-[var(--color-muted)]",
            )}
          >
            <PackageOpen className="h-4 w-4" /> Eşya
          </button>
          <button
            type="button"
            onClick={() => set("type", "container")}
            className={cn(
              "flex items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-medium",
              form.type === "container"
                ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                : "border-[var(--color-border)] text-[var(--color-muted)]",
            )}
          >
            <Box className="h-4 w-4" /> Kutu / Dolap
          </button>
        </div>

        {/* photo */}
        <div className="flex items-center gap-3">
          <div className="grid h-20 w-20 shrink-0 place-items-center overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)]">
            {form.photo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={form.photo || "/placeholder.svg"} alt="Eşya fotoğrafı" className="h-full w-full object-cover" />
            ) : (
              <ImageIcon className="h-7 w-7 text-[var(--color-muted)]" />
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => galleryRef.current?.click()} disabled={busy}>
              <ImageIcon className="h-4 w-4" /> Galeri
            </Button>
            <Button variant="outline" onClick={() => cameraRef.current?.click()} disabled={busy}>
              <Camera className="h-4 w-4" /> Kamera
            </Button>
            {form.photo && (
              <Button variant="ghost" onClick={() => set("photo", null)}>
                <Trash2 className="h-4 w-4" /> Kaldır
              </Button>
            )}
            <input
              ref={galleryRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/heic,image/heif"
              className="hidden"
              onChange={(e) => onPickFile(e.target.files?.[0])}
            />
            <input
              ref={cameraRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={(e) => onPickFile(e.target.files?.[0])}
            />
          </div>
        </div>

        <Field label="İsim">
          <Input value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="Örn: HDMI Kablosu" autoFocus />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Kategori">
            <Select value={form.category} onChange={(e) => set("category", e.target.value)}>
              <option value="">Seçilmedi</option>
              {CATEGORIES.map((c) => (
                <option key={c.key} value={c.key}>
                  {c.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Fiyat / Değer (₺)">
            <Input
              type="number"
              inputMode="decimal"
              value={form.price}
              onChange={(e) => set("price", e.target.value)}
              placeholder="0"
            />
          </Field>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <Field label="Miktar">
            <Input type="number" inputMode="numeric" value={form.quantity} onChange={(e) => set("quantity", e.target.value)} />
          </Field>
          <Field label="Birim">
            <Select value={form.unit} onChange={(e) => set("unit", e.target.value as Unit)}>
              {UNITS.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Min. Stok">
            <Input type="number" inputMode="numeric" value={form.minStock} onChange={(e) => set("minStock", e.target.value)} placeholder="—" />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Son Kullanma" hint="GG/AA/YYYY">
            <Input value={form.expiryDate} onChange={(e) => set("expiryDate", e.target.value)} placeholder="31/12/2026" />
          </Field>
          <Field label="Garanti Bitiş" hint="GG/AA/YYYY">
            <Input value={form.warrantyDate} onChange={(e) => set("warrantyDate", e.target.value)} placeholder="31/12/2026" />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Ödünç Verildi">
            <Input value={form.borrowedTo} onChange={(e) => set("borrowedTo", e.target.value)} placeholder="Kişi adı" />
          </Field>
          <Field label="Koli No (Taşınma)">
            <Input type="number" inputMode="numeric" value={form.boxNo} onChange={(e) => set("boxNo", e.target.value)} placeholder="—" />
          </Field>
        </div>

        <Field label="Etiketler" hint="Virgülle ayırın">
          <div className="relative">
            <Tag className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-[var(--color-muted)]" />
            <Input className="pl-9" value={form.tags} onChange={(e) => set("tags", e.target.value)} placeholder="acil, yedek, kırılabilir" />
          </div>
        </Field>

        <div>
          <span className="mb-2 block text-xs font-medium text-[var(--color-muted)]">Durum Bayrakları</span>
          <div className="flex flex-wrap gap-2">
            {flags.map((f) => {
              const active = form[f.key]
              const Icon = f.icon
              return (
                <button
                  key={f.key}
                  type="button"
                  onClick={() => set(f.key, !active)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors",
                    active ? "border-transparent text-white" : "border-[var(--color-border)] text-[var(--color-muted)]",
                  )}
                  style={active ? { backgroundColor: f.color } : undefined}
                >
                  <Icon className="h-3.5 w-3.5" /> {f.label}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </Modal>
  )
}
