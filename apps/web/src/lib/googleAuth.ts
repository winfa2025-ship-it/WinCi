/**
 * Google sign-in:
 * - Android Capacitor: @southdevs/capacitor-google-auth (native; WebView GIS is blocked)
 * - Web / PWA: Google Identity Services (GIS) One Tap / prompt
 */
import { getGoogleClientId } from './googleClientId'
import { isNativeApp } from './platform'

let gisLoading: Promise<void> | null = null

function loadGisScript(): Promise<void> {
  if ((window as any).google?.accounts?.id) return Promise.resolve()
  if (gisLoading) return gisLoading
  gisLoading = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-winci-gis]') as HTMLScriptElement | null
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('無法載入 Google Identity script')))
      return
    }
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.defer = true
    s.dataset.winciGis = '1'
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('無法載入 Google Identity script（檢查網絡）'))
    document.head.appendChild(s)
  })
  return gisLoading
}

async function signInNative(clientId: string): Promise<string> {
  // Dynamic import so web build does not hard-fail if plugin missing in some shells
  const mod = await import('@southdevs/capacitor-google-auth')
  const GoogleAuth = mod.GoogleAuth
  await GoogleAuth.initialize({
    clientId,
    scopes: ['profile', 'email'],
    grantOfflineAccess: false,
  })
  const user = await GoogleAuth.signIn()
  const idToken =
    (user as any)?.authentication?.idToken ||
    (user as any)?.idToken ||
    ''
  if (!idToken) {
    throw new Error('Google 未回傳 idToken。請確認已建立 Android OAuth client（package com.winci.app + debug SHA-1）同 Web Client ID。')
  }
  return idToken
}

function signInGis(clientId: string): Promise<string> {
  return new Promise(async (resolve, reject) => {
    try {
      await loadGisScript()
      const gis = (window as any).google?.accounts?.id
      if (!gis) {
        reject(new Error('Google Identity 未就緒'))
        return
      }
      let settled = false
      const timer = window.setTimeout(() => {
        if (!settled) {
          settled = true
          reject(new Error('Google 登入逾時／被取消。瀏覽器請允許彈窗；Android 請用原生 Google 登入。'))
        }
      }, 120_000)
      gis.initialize({
        client_id: clientId,
        callback: (resp: any) => {
          if (settled) return
          settled = true
          window.clearTimeout(timer)
          if (resp?.credential) resolve(resp.credential)
          else reject(new Error('Google 未回傳 credential'))
        },
        auto_select: false,
        cancel_on_tap_outside: true,
      })
      // Prefer button-less prompt; if suppressed, fall back to explicit render into a temp div
      gis.prompt((notification: any) => {
        try {
          if (notification?.isNotDisplayed?.() || notification?.isSkippedMoment?.()) {
            const host = document.getElementById('winci-gis-btn')
            if (host) {
              host.innerHTML = ''
              gis.renderButton(host, {
                theme: 'filled_black',
                size: 'large',
                text: 'signin_with',
                shape: 'rectangular',
                width: 280,
              })
            }
          }
        } catch {}
      })
    } catch (e: any) {
      reject(e instanceof Error ? e : new Error(String(e)))
    }
  })
}

/** Returns Google ID token (JWT) for POST /auth/google. */
export async function getGoogleIdToken(): Promise<string> {
  const clientId = getGoogleClientId()
  if (!clientId) {
    throw new Error(
      '未設定 Google Web Client ID。請去 Settings 貼上 Client ID，或用電郵登入／Demo 登入。詳見 docs/GOOGLE-LOGIN.md',
    )
  }
  if (isNativeApp()) {
    try {
      return await signInNative(clientId)
    } catch (e: any) {
      const msg = String(e?.message || e)
      // If native plugin missing, explain clearly (do NOT fall back to GIS in WebView — Google blocks it)
      throw new Error(
        msg.includes('idToken') || msg.includes('OAuth')
          ? msg
          : `Android Google 登入失敗：${msg}。請確認 Google Play 服務可用，並喺 Google Cloud 加咗 Android client（com.winci.app + SHA-1）。`,
      )
    }
  }
  return signInGis(clientId)
}
