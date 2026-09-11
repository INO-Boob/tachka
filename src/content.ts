export type SystemId = 'battery' | 'drive' | 'optics'
export const systems = {
  battery: {
    index: '01', label: 'Battery', category: 'Energy storage', title: 'The energy\nbeneath you.',
    short: 'Explore the battery pack',
    description: 'A traction battery stores electrical energy and supplies it to the drive system. In this concept, it sits low beneath the cabin.',
    benefit: 'A low, flat package leaves the cabin above it open.',
    image: '/media/battery-blue.png', anchor: { x: 64, y: 72 },
    points: [
      { label: 'Cell modules', text: 'Cells grouped into modules store the energy.', x: 31, y: 42 },
      { label: 'High-voltage connection', text: 'Orange connections mark the high-voltage electrical path in this illustration.', x: 27, y: 55 },
      { label: 'Protective enclosure', text: 'The pack housing supports and protects the assembly.', x: 49, y: 49 },
    ],
  },
  drive: {
    index: '02', label: 'Electric drive', category: 'Power delivery', title: 'Electricity,\ninto motion.',
    short: 'Explore the drive unit',
    description: 'The electric motor turns electrical energy into rotation. A reduction gear transfers that rotation to the wheels.',
    benefit: 'Control of motor torque gives the driver a responsive connection to the wheels.',
    image: '/media/drive-blue.png', anchor: { x: 25, y: 48 },
    points: [
      { label: 'Stator windings', text: 'Stationary windings create a rotating magnetic field.', x: 32, y: 46 },
      { label: 'Rotor', text: 'The rotor turns within the stator and drives the shaft.', x: 24, y: 49 },
      { label: 'Reduction gear', text: 'Gearing lowers rotational speed and increases wheel torque.', x: 48, y: 51 },
    ],
  },
  optics: {
    index: '03', label: 'Advanced lenses', category: 'Light & optics', title: 'Light,\nshaped precisely.',
    short: 'Explore the headlamp optics',
    description: 'Inside this concept headlamp, an LED module produces light and a projection lens shapes it into a controlled beam.',
    benefit: 'Precise light distribution helps illuminate the road where it is needed.',
    image: '/media/lenses-blue.png', anchor: { x: 36, y: 60 },
    points: [
      { label: 'Projection lens', text: 'The optical lens directs the light into the designed beam pattern.', x: 32.9, y: 55.7 },
      { label: 'LED module', text: 'The light source sits behind the projection optics.', x: 50.3, y: 57.2 },
      { label: 'Heat sink', text: 'Metal fins dissipate heat from the light-source assembly.', x: 61.9, y: 56.3 },
    ],
  },
} as const
export const systemIds: SystemId[] = ['battery', 'drive', 'optics']
export type HotspotId = SystemId | 'wheels' | 'paint'
export const hotspots: { id: HotspotId; index: string; label: string; anchor: { x: number; y: number }; target: SystemId | null }[] = [
  ...(['battery', 'drive'] as const).map(id => ({ id, index: systems[id].index, label: systems[id].label, anchor: systems[id].anchor, target: id })),
  { id: 'paint', index: '03', label: 'Body colour', anchor: { x: 55, y: 51 }, target: null },
  { id: 'wheels', index: '04', label: 'Wheel design', anchor: { x: 48, y: 71 }, target: null },
]

// Enable each pair only after first/last frames, crop and color have been checked.
export const clips: Record<SystemId, { forward: string; reverse: string; enabled: boolean }> = {
  battery: { forward: '/media/battery-forward.mp4', reverse: '/media/battery-reverse.mp4', enabled: false },
  drive: { forward: '/media/drive-forward.mp4', reverse: '/media/drive-reverse.mp4', enabled: false },
  optics: { forward: '/media/optics-forward.mp4', reverse: '/media/optics-reverse.mp4', enabled: false },
}
