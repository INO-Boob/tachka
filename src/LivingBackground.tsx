import { useEffect, useRef } from 'react'

// Ambient studio layer behind the scene. It never touches the image plane,
// so media coordinates and hotspots stay exactly where they were.
export default function LivingBackground({ reduced }: { reduced: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const element = canvas.current!
    const host = element.parentElement!
    const context = element.getContext('2d')!
    let width = 0, height = 0, ratio = 1, frame = 0, last = performance.now(), idle = 0
    const target = { x: .5, y: .38, active: false }
    const light = { x: .5, y: .38, energy: 0 }
    type Mote = { x: number; y: number; z: number; vx: number; vy: number; phase: number }
    let motes: Mote[] = []

    const resize = () => {
      ratio = Math.min(2, window.devicePixelRatio || 1)
      width = host.clientWidth; height = host.clientHeight
      element.width = Math.round(width * ratio); element.height = Math.round(height * ratio)
      const count = Math.round(Math.min(90, width * height / 16000))
      motes = Array.from({ length: count }, () => ({ x: Math.random() * width, y: Math.random() * height, z: .3 + Math.random() * .7, vx: (Math.random() - .5) * 6, vy: -2 - Math.random() * 6, phase: Math.random() * Math.PI * 2 }))
      if (reduced) draw(0)
    }

    const move = (event: PointerEvent) => {
      const box = host.getBoundingClientRect()
      target.x = (event.clientX - box.left) / box.width; target.y = (event.clientY - box.top) / box.height
      target.active = true; idle = 0
    }
    const leave = () => { target.active = false }

    function draw(dt: number) {
      context.setTransform(ratio, 0, 0, ratio, 0, 0)
      context.clearRect(0, 0, width, height)
      const lx = light.x * width, ly = light.y * height
      const reach = Math.max(width, height)

      // Broad soft key light that follows the cursor.
      const glow = context.createRadialGradient(lx, ly, 0, lx, ly, reach * .55)
      glow.addColorStop(0, `rgba(255,255,255,${.13 + light.energy * .05})`)
      glow.addColorStop(.35, 'rgba(225,234,240,.05)')
      glow.addColorStop(1, 'rgba(255,255,255,0)')
      context.fillStyle = glow; context.fillRect(0, 0, width, height)

      // Counter-light in the opposite corner keeps the studio from looking flat.
      const cx = width - lx * .6, cy = height - ly * .5
      const shade = context.createRadialGradient(cx, cy, 0, cx, cy, reach * .6)
      shade.addColorStop(0, 'rgba(36,62,82,.22)'); shade.addColorStop(1, 'rgba(36,62,82,0)')
      context.fillStyle = shade; context.fillRect(0, 0, width, height)

      // Fine dot grid with a gentle parallax; dots near the light swell slightly.
      const step = width <= 900 ? 26 : 32
      const ox = ((light.x - .5) * -14) % step, oy = ((light.y - .5) * -14) % step
      for (let y = oy - step; y < height + step; y += step) for (let x = ox - step; x < width + step; x += step) {
        const d = Math.hypot(x - lx, y - ly), near = Math.max(0, 1 - d / 260)
        const push = near * near * 7, angle = Math.atan2(y - ly, x - lx)
        context.fillStyle = near > .55 ? `rgba(237,255,57,${.1 + near * .35})` : `rgba(255,255,255,${.07 + near * .3})`
        context.beginPath(); context.arc(x + Math.cos(angle) * push, y + Math.sin(angle) * push, .7 + near * 1.1, 0, Math.PI * 2); context.fill()
      }

      // Slow dust motes catching the light, nudged away from the cursor.
      for (const mote of motes) {
        if (dt) {
          const dx = mote.x - lx, dy = mote.y - ly, d2 = dx * dx + dy * dy + 900
          const force = target.active ? 2600 / d2 : 0
          mote.vx += dx * force * dt; mote.vy += dy * force * dt
          mote.vx *= .985; mote.vy = mote.vy * .985 - .4 * dt * mote.z
          mote.x += (mote.vx + Math.sin(mote.phase += dt * .6) * 4) * dt * mote.z
          mote.y += mote.vy * dt * mote.z
          if (mote.y < -10) { mote.y = height + 10; mote.x = Math.random() * width; mote.vy = -2 - Math.random() * 6 }
          if (mote.x < -10) mote.x = width + 10; else if (mote.x > width + 10) mote.x = -10
        }
        const lit = Math.max(0, 1 - Math.hypot(mote.x - lx, mote.y - ly) / (reach * .45))
        context.fillStyle = `rgba(255,255,255,${(.08 + lit * .45) * mote.z})`
        context.beginPath(); context.arc(mote.x, mote.y, mote.z * 1.6, 0, Math.PI * 2); context.fill()
      }
    }

    function tick(now: number) {
      const dt = Math.min(.05, (now - last) / 1000); last = now
      idle += dt
      // Without a pointer the light drifts on its own, so phones still feel alive.
      if (!target.active && idle > 2.5) { const t = now / 1000; target.x = .5 + Math.sin(t * .23) * .28; target.y = .4 + Math.cos(t * .31) * .18 }
      const ease = 1 - Math.pow(.0025, dt)
      const before = light.x + light.y
      light.x += (target.x - light.x) * ease; light.y += (target.y - light.y) * ease
      light.energy += (Math.min(1, Math.abs(light.x + light.y - before) * 40) - light.energy) * ease
      host.style.setProperty('--light-x', `${(light.x * 100).toFixed(2)}%`)
      host.style.setProperty('--light-y', `${(light.y * 100).toFixed(2)}%`)
      draw(dt)
      frame = requestAnimationFrame(tick)
    }

    const visibility = () => {
      cancelAnimationFrame(frame)
      if (!document.hidden && !reduced) { last = performance.now(); frame = requestAnimationFrame(tick) }
    }

    resize()
    const observer = new ResizeObserver(resize); observer.observe(host)
    window.addEventListener('pointermove', move, { passive: true })
    window.addEventListener('pointerdown', move, { passive: true })
    document.documentElement.addEventListener('pointerleave', leave)
    document.addEventListener('visibilitychange', visibility)
    visibility()
    return () => {
      cancelAnimationFrame(frame); observer.disconnect()
      window.removeEventListener('pointermove', move); window.removeEventListener('pointerdown', move)
      document.documentElement.removeEventListener('pointerleave', leave)
      document.removeEventListener('visibilitychange', visibility)
    }
  }, [reduced])

  return <canvas ref={canvas} className="living-background" aria-hidden="true"/>
}
