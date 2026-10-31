/** Detect Capacitor native shell (Android / iOS). */
export function isNativeApp(): boolean {
  try {
    const w = window as any
    return !!(w.Capacitor?.isNativePlatform?.() || w.Capacitor?.getPlatform?.() === 'android' || w.Capacitor?.getPlatform?.() === 'ios')
  } catch {
    return false
  }
}

export function isAndroidApp(): boolean {
  try {
    const w = window as any
    return w.Capacitor?.getPlatform?.() === 'android' || /Android/i.test(navigator.userAgent) && isNativeApp()
  } catch {
    return false
  }
}
