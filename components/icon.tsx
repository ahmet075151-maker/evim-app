"use client"

import {
  Cpu,
  Armchair,
  Shirt,
  Book,
  Utensils,
  Flower,
  Flower2,
  FileText,
  Gamepad2,
  Dumbbell,
  Apple,
  SprayCan,
  Package,
  Sofa,
  CookingPot,
  BedDouble,
  Bath,
  Baby,
  Laptop,
  Car,
  Warehouse,
  DoorOpen,
  Home,
  Box,
  type LucideIcon,
} from "lucide-react"

const MAP: Record<string, LucideIcon> = {
  cpu: Cpu,
  armchair: Armchair,
  shirt: Shirt,
  book: Book,
  utensils: Utensils,
  flower: Flower,
  "flower-2": Flower2,
  "file-text": FileText,
  "gamepad-2": Gamepad2,
  dumbbell: Dumbbell,
  apple: Apple,
  "spray-can": SprayCan,
  package: Package,
  sofa: Sofa,
  "cooking-pot": CookingPot,
  "bed-double": BedDouble,
  bath: Bath,
  baby: Baby,
  laptop: Laptop,
  car: Car,
  warehouse: Warehouse,
  "door-open": DoorOpen,
  home: Home,
  box: Box,
}

export function DynIcon({
  name,
  className,
  style,
}: {
  name?: string
  className?: string
  style?: React.CSSProperties
}) {
  const Cmp = (name && MAP[name]) || Package
  return <Cmp className={className} style={style} />
}
