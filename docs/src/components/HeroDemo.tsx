import { useEffect, useRef, useState } from 'react'
import { Mic, RotateCcw, Square, Volume2 } from 'lucide-react'
import { Bird } from './Bird'
import { Waveform } from './Waveform'

/** Audio pregrabado de la simulación. Coloca los archivos en /public/audio. */
const INPUT_AUDIO = `${import.meta.env.BASE_URL}audio/voz-original.mp3`
const OUTPUT_AUDIO = `${import.meta.env.BASE_URL}audio/voz-myna.mp3`
const TRANSCRIPT = 'Hola, ¿me escucháis bien?'

type Phase = 'idle' | 'recording' | 'ready' | 'speaking'

const STATUS: Record<Phase, string> = {
  idle: 'Pulsa el micro',
  recording: 'Grabando',
  ready: 'Transcrito',
  speaking: 'Reproduciendo',
}

/** Fallback si falta el mp3: usa la voz del navegador para que la demo siga funcionando. */
function speak(text: string, pitch: number, onEnd: () => void) {
  if (!('speechSynthesis' in window)) {
    globalThis.setTimeout(onEnd, 2200)
    return
  }
  const u = new SpeechSynthesisUtterance(text)
  u.lang = 'es-ES'
  u.pitch = pitch
  u.onend = onEnd
  u.onerror = onEnd
  window.speechSynthesis.cancel()
  window.speechSynthesis.speak(u)
}

export function HeroDemo() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [typed, setTyped] = useState('')
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const timerRef = useRef<number | null>(null)

  const stopAll = () => {
    audioRef.current?.pause()
    audioRef.current = null
    if (timerRef.current) window.clearInterval(timerRef.current)
    timerRef.current = null
    if ('speechSynthesis' in window) window.speechSynthesis.cancel()
  }

  useEffect(() => stopAll, [])

  const finishRecording = () => {
    if (timerRef.current) window.clearInterval(timerRef.current)
    timerRef.current = null
    setTyped(TRANSCRIPT)
    setPhase('ready')
  }

  /** Escribe la transcripción a lo largo de `durationMs`. */
  const typeOver = (durationMs: number) => {
    const start = performance.now()
    if (timerRef.current) window.clearInterval(timerRef.current)
    timerRef.current = window.setInterval(() => {
      const p = Math.min(1, (performance.now() - start) / durationMs)
      setTyped(TRANSCRIPT.slice(0, Math.round(p * TRANSCRIPT.length)))
      if (p >= 1 && timerRef.current) window.clearInterval(timerRef.current)
    }, 40)
  }

  const record = () => {
    if (phase === 'recording') {
      stopAll()
      finishRecording()
      return
    }
    stopAll()
    setTyped('')
    setPhase('recording')

    const audio = new Audio(INPUT_AUDIO)
    audioRef.current = audio
    audio.addEventListener('loadedmetadata', () => {
      // Deja un pequeño margen para que el texto termine algo antes que la voz.
      typeOver(Math.max(800, audio.duration * 1000 * 0.9))
    })
    audio.addEventListener('ended', finishRecording)
    audio.play().catch(() => {
      audioRef.current = null
      typeOver(2000)
      speak(TRANSCRIPT, 1, finishRecording)
    })
  }

  const playOutput = () => {
    if (phase === 'speaking') {
      stopAll()
      setPhase('ready')
      return
    }
    stopAll()
    setPhase('speaking')
    const done = () => setPhase('ready')
    const audio = new Audio(OUTPUT_AUDIO)
    audioRef.current = audio
    audio.addEventListener('ended', done)
    audio.play().catch(() => {
      audioRef.current = null
      speak(TRANSCRIPT, 0.4, done)
    })
  }

  const reset = () => {
    stopAll()
    setTyped('')
    setPhase('idle')
  }

  const recording = phase === 'recording'
  const speaking = phase === 'speaking'
  const hasOutput = phase === 'ready' || phase === 'speaking'

  return (
    <div className="rise relative" style={{ animationDelay: '150ms' }}>
      <div className="relative overflow-hidden rounded-[1.75rem] border border-ink/10 bg-white sm:rounded-[2rem] shadow-[0_40px_80px_-40px_rgba(28,30,38,0.35)]">
        <div className="grain absolute inset-0" />
        <div
          className={`absolute left-1/2 top-[42%] size-72 -translate-x-1/2 -translate-y-1/2 rounded-full blur-3xl transition-colors duration-700 ${
            recording ? 'bg-red-400/25' : 'bg-myna/30'
          }`}
        />

        <div className="relative flex items-center justify-between px-5 pt-5 font-mono sm:px-6 text-[11px] uppercase tracking-[0.14em] text-ink/50">
          <span className="flex items-center gap-2" aria-live="polite">
            <span className="relative flex size-2">
              {(recording || speaking) && (
                <span
                  className={`absolute inline-flex size-full animate-ping rounded-full ${recording ? 'bg-red-500/60' : 'bg-myna'}`}
                />
              )}
              <span
                className={`relative inline-flex size-2 rounded-full transition-colors ${
                  recording ? 'bg-red-500' : speaking ? 'bg-myna' : hasOutput ? 'bg-emerald-500' : 'bg-ink/25'
                }`}
              />
            </span>
            <span className={recording ? 'text-red-500' : ''}>{STATUS[phase]}</span>
          </span>
          {phase !== 'idle' ? (
            <button
              onClick={reset}
              className="flex items-center gap-1.5 rounded-full px-2 py-1 transition hover:bg-ink/5 hover:text-ink"
            >
              <RotateCcw className="size-3" /> Reiniciar
            </button>
          ) : (
            <span>myna · local</span>
          )}
        </div>

        <div className="relative flex justify-center px-10 pb-2 pt-4 sm:pb-4 sm:pt-6">
          <Bird className="w-44 sm:w-64" />
        </div>

        <div className="relative space-y-2.5 px-3 pb-3 sm:px-5 sm:pb-5">
          {/* Entrada: micrófono */}
          <div
            className={`flex items-center gap-3 rounded-2xl border bg-paper/80 px-3 py-3 backdrop-blur transition-colors ${
              recording ? 'border-red-500/30' : 'border-ink/10'
            }`}
          >
            <button
              onClick={record}
              aria-label={recording ? 'Detener grabación' : 'Grabar'}
              className={`relative grid size-10 shrink-0 cursor-pointer place-items-center rounded-full transition-all duration-300 hover:scale-105 ${
                recording ? 'bg-red-500 text-white' : 'bg-ink text-paper'
              }`}
            >
              {recording && <span className="absolute inset-0 animate-ping rounded-full bg-red-500/40" />}
              {recording ? <Square className="relative size-3.5 fill-current" /> : <Mic className="size-4" />}
            </button>
            <p className="min-w-0 flex-1 truncate text-sm text-ink/80">
              {phase === 'idle' ? (
                <span className="text-ink/40">Pulsa para grabar…</span>
              ) : (
                <>
                  {typed}
                  {recording && <span className="caret ml-0.5 inline-block h-4 w-px translate-y-0.5 bg-ink" />}
                </>
              )}
            </p>
            <Waveform count={10} color={recording ? 'bg-red-500' : 'bg-ink'} active={recording} className="max-[380px]:hidden" />
          </div>

          {/* Salida: otra voz */}
          <div
            className={`grid transition-all duration-500 ease-out ${
              hasOutput ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
            }`}
          >
            <div className="overflow-hidden">
              <div className="flex items-center gap-3 rounded-2xl bg-ink px-3 py-3 text-paper">
                <button
                  onClick={playOutput}
                  disabled={!hasOutput}
                  aria-label={speaking ? 'Detener' : 'Escuchar la otra voz'}
                  className="relative grid size-10 shrink-0 cursor-pointer place-items-center rounded-full bg-myna text-ink transition-transform duration-300 hover:scale-105"
                >
                  {speaking && <span className="absolute inset-0 animate-ping rounded-full bg-myna/40" />}
                  {speaking ? <Square className="relative size-3.5 fill-current" /> : <Volume2 className="size-4" />}
                </button>
                <div className="min-w-0 flex-1">
                  <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-paper/40">Voz generada</p>
                  <p className="truncate text-sm">{TRANSCRIPT}</p>
                </div>
                <Waveform count={10} color="bg-myna" active={speaking} className="max-[380px]:hidden" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
