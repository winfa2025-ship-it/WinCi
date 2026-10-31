/** Google Web Client ID — Settings override → Vite env → empty. */
const KEY = 'winci_google_client_id'

export function getGoogleClientId(): string {
  try {
    const saved = localStorage.getItem(KEY)
    if (saved != null && saved.trim() !== '') return saved.trim()
  } catch {}
  return ((import.meta as any).env?.VITE_GOOGLE_CLIENT_ID as string | undefined)?.trim() || ''
}

export function setGoogleClientIdLocal(id: string | null) {
  try {
    if (id == null || id.trim() === '') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, id.trim())
  } catch {}
}
