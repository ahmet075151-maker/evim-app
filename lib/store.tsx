"use client"

import { createContext, useContext, useEffect, useMemo, useReducer, useRef, useState, type ReactNode } from "react"
import { get, set } from "idb-keyval"
import type { AppState, InvNode, NodeType, TrashEntry } from "./types"
import { uid } from "./utils"
import { guessRoomType } from "./taxonomy"

const STORAGE_KEY = "evim-state-v1"

const initialState: AppState = {
  nodes: [],
  trash: [],
  guestMode: false,
  version: 1,
}

type Action =
  | { type: "HYDRATE"; state: AppState }
  | { type: "ADD"; node: InvNode }
  | { type: "UPDATE"; id: string; patch: Partial<InvNode> }
  | { type: "DELETE"; ids: string[] }
  | { type: "MOVE"; ids: string[]; newParentId: string | null }
  | { type: "RESTORE"; trashId: string }
  | { type: "CLEAR_TRASH" }
  | { type: "SET_GUEST"; value: boolean }
  | { type: "IMPORT"; state: AppState }

function collectSubtree(nodes: InvNode[], rootId: string): InvNode[] {
  const result: InvNode[] = []
  const stack = [rootId]
  while (stack.length) {
    const id = stack.pop()!
    const node = nodes.find((n) => n.id === id)
    if (node) {
      result.push(node)
      nodes.filter((n) => n.parentId === id).forEach((c) => stack.push(c.id))
    }
  }
  return result
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "HYDRATE":
      return action.state
    case "IMPORT":
      return { ...action.state, version: 1 }
    case "ADD":
      return { ...state, nodes: [...state.nodes, action.node] }
    case "UPDATE":
      return {
        ...state,
        nodes: state.nodes.map((n) =>
          n.id === action.id ? { ...n, ...action.patch, updatedAt: Date.now() } : n,
        ),
      }
    case "DELETE": {
      const toRemove = new Set<string>()
      const entries: TrashEntry[] = []
      for (const id of action.ids) {
        const subtree = collectSubtree(state.nodes, id)
        if (!subtree.length) continue
        subtree.forEach((n) => toRemove.add(n.id))
        entries.push({
          id: uid(),
          deletedAt: Date.now(),
          nodes: subtree,
          rootName: subtree[0].name,
          rootType: subtree[0].type,
        })
      }
      return {
        ...state,
        nodes: state.nodes.filter((n) => !toRemove.has(n.id)),
        trash: [...entries, ...state.trash],
      }
    }
    case "MOVE":
      return {
        ...state,
        nodes: state.nodes.map((n) =>
          action.ids.includes(n.id) ? { ...n, parentId: action.newParentId, updatedAt: Date.now() } : n,
        ),
      }
    case "RESTORE": {
      const entry = state.trash.find((t) => t.id === action.trashId)
      if (!entry) return state
      const existingIds = new Set(state.nodes.map((n) => n.id))
      // if original parent gone, restore root to top-level (room becomes room; item to null → shown nowhere, so keep parent if exists else null)
      const restored = entry.nodes.map((n) => {
        if (n.id === entry.nodes[0].id) {
          const parentExists = n.parentId ? existingIds.has(n.parentId) : true
          return parentExists ? n : { ...n, parentId: null, type: (n.type === "item" ? "room" : n.type) as NodeType }
        }
        return n
      })
      return {
        ...state,
        nodes: [...state.nodes, ...restored.filter((n) => !existingIds.has(n.id))],
        trash: state.trash.filter((t) => t.id !== action.trashId),
      }
    }
    case "CLEAR_TRASH":
      return { ...state, trash: [] }
    case "SET_GUEST":
      return { ...state, guestMode: action.value }
    default:
      return state
  }
}

interface StoreContextValue {
  state: AppState
  ready: boolean
  addRoom: (name: string) => InvNode
  addNode: (input: Partial<InvNode> & { name: string; type: NodeType; parentId: string | null }) => InvNode
  updateNode: (id: string, patch: Partial<InvNode>) => void
  deleteNodes: (ids: string[]) => void
  moveNodes: (ids: string[], newParentId: string | null) => void
  restoreTrash: (trashId: string) => void
  clearTrash: () => void
  setGuest: (v: boolean) => void
  importState: (s: AppState) => void
  childrenOf: (parentId: string | null) => InvNode[]
  nodeById: (id: string) => InvNode | undefined
  pathTo: (id: string) => InvNode[]
  descendants: (id: string) => InvNode[]
}

const StoreContext = createContext<StoreContextValue | null>(null)

let codeCounter = 0
function genCode(nodes: InvNode[]) {
  // find max existing K-xxxx
  let max = 0
  for (const n of nodes) {
    const m = n.code?.match(/^K-(\d+)$/)
    if (m) max = Math.max(max, Number(m[1]))
  }
  codeCounter = Math.max(codeCounter, max)
  codeCounter += 1
  return `K-${String(codeCounter).padStart(4, "0")}`
}

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const [ready, setReady] = useState(false)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    let mounted = true
    get<AppState>(STORAGE_KEY).then((stored) => {
      if (mounted && stored && stored.nodes) {
        dispatch({ type: "HYDRATE", state: { ...initialState, ...stored } })
      }
      if (mounted) setReady(true)
    })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    if (!ready) return
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => {
      set(STORAGE_KEY, state).catch((e) => console.log("[v0] save error", e))
    }, 250)
  }, [state, ready])

  const value = useMemo<StoreContextValue>(() => {
    const nodeById = (id: string) => state.nodes.find((n) => n.id === id)
    return {
      state,
      ready,
      addRoom: (name: string) => {
        const rt = guessRoomType(name)
        const node: InvNode = {
          id: uid(),
          type: "room",
          name: name.trim() || "Yeni Oda",
          parentId: null,
          roomType: rt.key,
          color: rt.color,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        }
        dispatch({ type: "ADD", node })
        return node
      },
      addNode: (input) => {
        const node: InvNode = {
          id: uid(),
          type: input.type,
          name: input.name.trim(),
          parentId: input.parentId,
          category: input.category,
          code: input.type !== "room" ? input.code || genCode(state.nodes) : undefined,
          price: input.price,
          quantity: input.quantity ?? 1,
          unit: input.unit ?? "Adet",
          minStock: input.minStock,
          expiryDate: input.expiryDate ?? null,
          warrantyDate: input.warrantyDate ?? null,
          borrowedTo: input.borrowedTo,
          tags: input.tags ?? [],
          favorite: input.favorite ?? false,
          forSale: input.forSale ?? false,
          donation: input.donation ?? false,
          lost: input.lost ?? false,
          boxNo: input.boxNo ?? null,
          photo: input.photo ?? null,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        }
        dispatch({ type: "ADD", node })
        return node
      },
      updateNode: (id, patch) => dispatch({ type: "UPDATE", id, patch }),
      deleteNodes: (ids) => dispatch({ type: "DELETE", ids }),
      moveNodes: (ids, newParentId) => dispatch({ type: "MOVE", ids, newParentId }),
      restoreTrash: (trashId) => dispatch({ type: "RESTORE", trashId }),
      clearTrash: () => dispatch({ type: "CLEAR_TRASH" }),
      setGuest: (v) => dispatch({ type: "SET_GUEST", value: v }),
      importState: (s) => dispatch({ type: "IMPORT", state: s }),
      childrenOf: (parentId) => state.nodes.filter((n) => n.parentId === parentId),
      nodeById,
      pathTo: (id) => {
        const path: InvNode[] = []
        let cur = nodeById(id)
        while (cur) {
          path.unshift(cur)
          cur = cur.parentId ? nodeById(cur.parentId) : undefined
        }
        return path
      },
      descendants: (id) => collectSubtree(state.nodes, id).filter((n) => n.id !== id),
    }
  }, [state, ready])

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}

export function useStore() {
  const ctx = useContext(StoreContext)
  if (!ctx) throw new Error("useStore must be used within StoreProvider")
  return ctx
}
