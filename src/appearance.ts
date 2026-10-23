export type AppearanceMode = 'paint' | 'wheels'
export const baseExterior = 'media/exterior-polished.png'
export type AppearanceOption = { id: string; label: string; image: string; color?: string }
export const appearanceOptions: Record<AppearanceMode, AppearanceOption[]> = {
  paint: [
    { id: 'silver', label: 'Studio Silver', color: '#c3c8cc', image: baseExterior },
    { id: 'electric', label: 'Electric Green', color: '#d6ee1e', image: 'media/config/electric-green.png' },
    { id: 'lime', label: 'Lime Green', color: '#7cc21f', image: 'media/config/lime-green.png' },
    { id: 'sky', label: 'Sky Blue', color: '#6f9bc0', image: 'media/config/sky-blue.png' },
    { id: 'graphite', label: 'Graphite', color: '#3a4148', image: 'media/config/graphite.png' },
  ],
  wheels: [
    { id: 'original', label: 'Multi-spoke', image: baseExterior },
    { id: 'aero', label: 'Aero Disc', image: 'media/config/wheels-aero.png' },
    { id: 'forged', label: 'Sport Forged', image: 'media/config/wheels-forged.png' },
  ],
}

export function canUseHotspot(active: AppearanceMode | null, id: string, closing: boolean) {
  return !closing && (!active || active === id)
}
