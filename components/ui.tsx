"use client"

import { useEffect, type ButtonHTMLAttributes, type ReactNode } from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "outline"

export function Button({
  variant = "secondary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium px-3.5 py-2.5 transition-colors disabled:opacity-40 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-background)]"
  const variants: Record<ButtonVariant, string> = {
    primary: "bg-[var(--color-primary)] text-[var(--color-primary-fg)] hover:opacity-90",
    secondary: "bg-[var(--color-surface-2)] text-[var(--color-foreground)] hover:bg-[var(--color-border)]",
    ghost: "text-[var(--color-foreground)] hover:bg-[var(--color-surface-2)]",
    outline: "border border-[var(--color-border)] hover:bg-[var(--color-surface-2)]",
    danger: "bg-[var(--color-danger)] text-white hover:opacity-90",
  }
  return <button className={cn(base, variants[variant], className)} {...props} />
}

export function IconButton({
  className,
  label,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex h-10 w-10 items-center justify-center rounded-xl text-[var(--color-foreground)] transition-colors hover:bg-[var(--color-surface-2)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]",
        className,
      )}
      {...props}
    />
  )
}

export function Badge({
  children,
  color,
  className,
}: {
  children: ReactNode
  color?: string
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold leading-none",
        className,
      )}
      style={
        color
          ? { backgroundColor: `${color}22`, color }
          : { backgroundColor: "var(--color-surface-2)", color: "var(--color-muted)" }
      }
    >
      {children}
    </span>
  )
}

export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
  wide,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  footer?: ReactNode
  wide?: boolean
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          "relative z-10 flex max-h-[92vh] w-full flex-col rounded-t-2xl sm:rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl animate-slide-up",
          wide ? "sm:max-w-2xl" : "sm:max-w-md",
        )}
      >
        <div className="flex items-center justify-between border-b border-[var(--color-border)] px-5 py-4">
          <h2 className="text-base font-semibold">{title}</h2>
          <IconButton label="Kapat" onClick={onClose}>
            <X className="h-5 w-5" />
          </IconButton>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>
        {footer && <div className="border-t border-[var(--color-border)] px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs font-medium text-[var(--color-muted)]">{label}</span>
      {children}
      {hint && <span className="block text-[11px] text-[var(--color-muted)]">{hint}</span>}
    </label>
  )
}

const inputCls =
  "w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm text-[var(--color-foreground)] placeholder:text-[var(--color-muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(inputCls, props.className)} {...props} />
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(inputCls, "min-h-20 resize-y", props.className)} {...props} />
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn(inputCls, "appearance-none", props.className)} {...props} />
}

export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  label: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="inline-flex items-center gap-2 text-sm"
    >
      <span
        className={cn(
          "relative h-6 w-11 rounded-full transition-colors",
          checked ? "bg-[var(--color-primary)]" : "bg-[var(--color-surface-2)]",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-[22px]" : "translate-x-0.5",
          )}
        />
      </span>
      <span>{label}</span>
    </button>
  )
}

export function EmptyState({ icon, title, hint }: { icon: ReactNode; title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-[var(--color-border)] px-6 py-14 text-center">
      <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[var(--color-surface-2)] text-[var(--color-muted)]">
        {icon}
      </div>
      <p className="font-medium">{title}</p>
      {hint && <p className="max-w-xs text-sm text-[var(--color-muted)]">{hint}</p>}
    </div>
  )
}
