// Reads an image file, auto-orients via bitmap, downscales longest edge to 1600px
// and compresses to JPEG at 0.85 quality. Returns a base64 data URL.
export async function processImageFile(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file).catch(() => null)
  if (!bitmap) {
    // fallback: read raw as data url (e.g. formats the browser can't decode)
    return await readAsDataURL(file)
  }
  const MAX = 1600
  let { width, height } = bitmap
  const scale = Math.min(1, MAX / Math.max(width, height))
  width = Math.round(width * scale)
  height = Math.round(height * scale)

  const canvas = document.createElement("canvas")
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext("2d")
  if (!ctx) return await readAsDataURL(file)
  ctx.drawImage(bitmap, 0, 0, width, height)
  bitmap.close?.()
  return canvas.toDataURL("image/jpeg", 0.85)
}

function readAsDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
