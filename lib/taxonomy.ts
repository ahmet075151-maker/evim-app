import type { Unit } from "./types"

export const UNITS: Unit[] = ["Adet", "Kutu", "Kg", "Litre", "Paket", "Çuval", "Şişe"]

export interface Category {
  key: string
  label: string
  color: string // tailwind-ish hex
  icon: string // lucide icon name key handled in component
}

export const CATEGORIES: Category[] = [
  { key: "elektronik", label: "Elektronik", color: "#3b82f6", icon: "cpu" },
  { key: "mobilya", label: "Mobilya", color: "#a16207", icon: "armchair" },
  { key: "giyim", label: "Giyim", color: "#ec4899", icon: "shirt" },
  { key: "kitap", label: "Kitap", color: "#8b5cf6", icon: "book" },
  { key: "mutfak", label: "Mutfak Eşyası", color: "#f97316", icon: "utensils" },
  { key: "dekorasyon", label: "Dekorasyon", color: "#14b8a6", icon: "flower" },
  { key: "belge", label: "Belge", color: "#64748b", icon: "file-text" },
  { key: "oyuncak", label: "Oyuncak", color: "#eab308", icon: "gamepad-2" },
  { key: "spor", label: "Spor", color: "#22c55e", icon: "dumbbell" },
  { key: "gida", label: "Gıda", color: "#ef4444", icon: "apple" },
  { key: "temizlik", label: "Temizlik", color: "#06b6d4", icon: "spray-can" },
  { key: "diger", label: "Diğer", color: "#94a3b8", icon: "package" },
]

export function categoryByKey(key?: string): Category | undefined {
  return CATEGORIES.find((c) => c.key === key)
}

export interface RoomType {
  key: string
  label: string
  color: string
  icon: string
  keywords: string[]
}

export const ROOM_TYPES: RoomType[] = [
  { key: "salon", label: "Salon", color: "#6366f1", icon: "sofa", keywords: ["salon", "oturma", "living"] },
  { key: "mutfak", label: "Mutfak", color: "#f97316", icon: "cooking-pot", keywords: ["mutfak", "kitchen"] },
  { key: "yatak", label: "Yatak Odası", color: "#8b5cf6", icon: "bed-double", keywords: ["yatak", "uyku", "bedroom"] },
  { key: "banyo", label: "Banyo", color: "#06b6d4", icon: "bath", keywords: ["banyo", "tuvalet", "wc", "lavabo", "bath"] },
  { key: "cocuk", label: "Çocuk Odası", color: "#eab308", icon: "baby", keywords: ["çocuk", "bebek", "cocuk", "kids"] },
  { key: "calisma", label: "Çalışma Odası", color: "#3b82f6", icon: "laptop", keywords: ["çalışma", "ofis", "büro", "calisma", "office", "study"] },
  { key: "giyinme", label: "Giyinme Odası", color: "#ec4899", icon: "shirt", keywords: ["giyinme", "gardırop", "dolap odası"] },
  { key: "balkon", label: "Balkon", color: "#22c55e", icon: "flower-2", keywords: ["balkon", "teras", "bahçe", "balcony"] },
  { key: "garaj", label: "Garaj", color: "#64748b", icon: "car", keywords: ["garaj", "araba", "garage"] },
  { key: "depo", label: "Depo", color: "#a16207", icon: "warehouse", keywords: ["depo", "kiler", "ambar", "storage"] },
  { key: "antre", label: "Antre / Hol", color: "#14b8a6", icon: "door-open", keywords: ["antre", "hol", "koridor", "giriş"] },
  { key: "diger", label: "Diğer Oda", color: "#94a3b8", icon: "home", keywords: [] },
]

export function guessRoomType(name: string): RoomType {
  const n = name.toLocaleLowerCase("tr")
  for (const rt of ROOM_TYPES) {
    if (rt.keywords.some((k) => n.includes(k))) return rt
  }
  return ROOM_TYPES[ROOM_TYPES.length - 1]
}

export function roomTypeByKey(key?: string): RoomType {
  return ROOM_TYPES.find((r) => r.key === key) ?? ROOM_TYPES[ROOM_TYPES.length - 1]
}
