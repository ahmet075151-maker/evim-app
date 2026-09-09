import type { AppState, InvNode } from "./types"
import { roomTypeByKey, categoryByKey } from "./taxonomy"

function pathString(nodes: InvNode[], node: InvNode): string {
  const parts: string[] = []
  let cur: InvNode | undefined = node
  const byId = new Map(nodes.map((n) => [n.id, n]))
  while (cur) {
    parts.unshift(cur.name)
    cur = cur.parentId ? byId.get(cur.parentId) : undefined
  }
  return parts.join(" › ")
}

function esc(v: unknown): string {
  const s = v == null ? "" : String(v)
  if (s.includes(";") || s.includes('"') || s.includes("\n")) {
    return '"' + s.replace(/"/g, '""') + '"'
  }
  return s
}

export function toCsv(state: AppState): string {
  const headers = [
    "Kod",
    "İsim",
    "Tür",
    "Konum",
    "Kategori",
    "Fiyat",
    "Miktar",
    "Birim",
    "Min Stok",
    "SKT/Garanti",
    "Ödünç",
    "Koli No",
    "Etiketler",
    "Favori",
    "Satılık",
    "Bağış",
    "Kayıp",
  ]
  const rows = state.nodes
    .filter((n) => n.type !== "room")
    .map((n) =>
      [
        n.code,
        n.name,
        n.type === "container" ? "Kutu" : "Eşya",
        pathString(state.nodes, n),
        categoryByKey(n.category)?.label ?? "",
        n.price ?? "",
        n.quantity ?? "",
        n.unit ?? "",
        n.minStock ?? "",
        n.expiryDate ?? n.warrantyDate ?? "",
        n.borrowedTo ?? "",
        n.boxNo ?? "",
        (n.tags ?? []).join(", "),
        n.favorite ? "Evet" : "",
        n.forSale ? "Evet" : "",
        n.donation ? "Evet" : "",
        n.lost ? "Evet" : "",
      ]
        .map(esc)
        .join(";"),
    )
  return "\uFEFF" + [headers.join(";"), ...rows].join("\n")
}

export function download(filename: string, content: string, mime = "text/plain") {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function timestampName(prefix: string, ext: string) {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, "0")
  return `${prefix}_${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}.${ext}`
}

export { roomTypeByKey }
