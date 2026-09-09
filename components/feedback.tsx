"use client"

import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react"
import { CheckCircle2, Info, AlertTriangle } from "lucide-react"
import { Button, Modal } from "./ui"

type ToastKind = "success" | "info" | "warn"
interface Toast {
  id: number
  msg: string
  kind: ToastKind
}

interface ConfirmOpts {
  title: string
  message: string
  confirmLabel?: string
  danger?: boolean
}

interface FeedbackCtx {
  toast: (msg: string, kind?: ToastKind) => void
  confirm: (opts: ConfirmOpts) => Promise<boolean>
}

const Ctx = createContext<FeedbackCtx | null>(null)

export function FeedbackProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const [confirmState, setConfirmState] = useState<ConfirmOpts | null>(null)
  const resolver = useRef<((v: boolean) => void) | null>(null)
  const counter = useRef(0)

  const toast = useCallback((msg: string, kind: ToastKind = "success") => {
    const id = ++counter.current
    setToasts((t) => [...t, { id, msg, kind }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 2800)
  }, [])

  const confirm = useCallback((opts: ConfirmOpts) => {
    setConfirmState(opts)
    return new Promise<boolean>((resolve) => {
      resolver.current = resolve
    })
  }, [])

  const close = (v: boolean) => {
    resolver.current?.(v)
    resolver.current = null
    setConfirmState(null)
  }

  const icons = {
    success: <CheckCircle2 className="h-5 w-5 text-[var(--color-success)]" />,
    info: <Info className="h-5 w-5 text-[var(--color-primary)]" />,
    warn: <AlertTriangle className="h-5 w-5 text-[var(--color-warning)]" />,
  }

  return (
    <Ctx.Provider value={{ toast, confirm }}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-6 z-[60] flex flex-col items-center gap-2 px-4">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto flex items-center gap-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm shadow-xl animate-slide-up"
          >
            {icons[t.kind]}
            <span>{t.msg}</span>
          </div>
        ))}
      </div>
      <Modal
        open={!!confirmState}
        onClose={() => close(false)}
        title={confirmState?.title ?? ""}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => close(false)}>
              Vazgeç
            </Button>
            <Button variant={confirmState?.danger ? "danger" : "primary"} onClick={() => close(true)}>
              {confirmState?.confirmLabel ?? "Onayla"}
            </Button>
          </div>
        }
      >
        <p className="text-sm text-[var(--color-muted)]">{confirmState?.message}</p>
      </Modal>
    </Ctx.Provider>
  )
}

export function useFeedback() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error("useFeedback must be used within FeedbackProvider")
  return ctx
}
