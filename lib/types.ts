export type NodeType = "room" | "container" | "item"

export type Unit = "Adet" | "Kutu" | "Kg" | "Litre" | "Paket" | "Çuval" | "Şişe"

export interface InvNode {
  id: string
  type: NodeType
  name: string
  parentId: string | null
  // room specific
  roomType?: string
  color?: string
  // item / container fields
  category?: string
  code?: string
  price?: number
  quantity?: number
  unit?: Unit
  minStock?: number
  expiryDate?: string | null
  warrantyDate?: string | null
  borrowedTo?: string
  tags?: string[]
  favorite?: boolean
  forSale?: boolean
  donation?: boolean
  lost?: boolean
  boxNo?: number | null
  photo?: string | null
  createdAt: number
  updatedAt: number
}

export interface TrashEntry {
  id: string
  deletedAt: number
  // full subtree that was removed, first element is the root that was deleted
  nodes: InvNode[]
  rootName: string
  rootType: NodeType
}

export interface AppState {
  nodes: InvNode[]
  trash: TrashEntry[]
  guestMode: boolean
  version: number
}
