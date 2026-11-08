import {
  ArrowUpRight,
  Cable,
  Cpu,
  Fish,
  Headphones,
  Keyboard,
  LibraryBig,
  Lock,
  SlidersHorizontal,
  Zap,
} from 'lucide-react'
import { Github } from './components/GithubIcon'
import { HeroDemo } from './components/HeroDemo'
import { Waveform } from './components/Waveform'

const GITHUB = 'https://github.com/MikeTrollYT/Myna'
const LOGO = `${import.meta.env.BASE_URL}logo.svg`

const steps = [
  {
    n: '01',
    icon: Keyboard,
    title: 'Mantén y habla',
    text: 'Pulsa tu tecla para hablar (F9 por defecto) o el botón de la ventana y di lo que quieras.',
  },
  {
    n: '02',
    icon: Cpu,
    title: 'Whisper transcribe',
    text: 'Tu voz se convierte en texto en tu propio equipo, por trozos y mientras hablas.',
  },
  {
    n: '03',
    icon: Fish,
    title: 'Fish Audio pone la voz',
    text: 'Al soltar, el texto viaja a Fish Audio y vuelve con la voz que hayas elegido.',
  },
  {
    n: '04',
    icon: Cable,
    title: 'Suena donde quieras',
    text: 'Envíalo a un cable virtual y úsalo como micrófono en Discord, OBS, juegos o videollamadas.',
  },
]

const features = [
  {
    icon: Lock,
    title: 'Transcripción local',
    text: 'Whisper corre en tu equipo, del modelo más ligero al más preciso. Tu audio no sale de él.',
  },
  {
    icon: LibraryBig,
    title: 'Biblioteca de voces',
    text: 'Guarda todas las voces de Fish Audio que quieras, con su foto, y cambia entre ellas con un clic.',
  },
  {
    icon: Headphones,
    title: 'Autoescucha',
    text: 'Oye en tus auriculares lo mismo que reciben los demás, al momento.',
  },
  {
    icon: SlidersHorizontal,
    title: 'Ajustado a tu micro',
    text: 'Medidor de nivel y sensibilidad ajustable para ignorar el ruido de fondo.',
  },
  {
    icon: Zap,
    title: 'Respuesta en streaming',
    text: 'La voz empieza a sonar mientras Fish Audio todavía está generando el resto.',
  },
  {
    icon: Github,
    title: 'Código abierto',
    text: 'Revisa el código, propón mejoras o adáptalo a lo que necesites.',
  },
]

function GithubButton({ dark = true }: { dark?: boolean }) {
  return (
    <a
      href={GITHUB}
      target="_blank"
      rel="noreferrer"
      className={`group inline-flex h-12 items-center gap-2.5 rounded-full pl-5 pr-2 text-[15px] font-medium transition-all duration-300 hover:-translate-y-0.5 ${
        dark ? 'bg-ink text-paper hover:shadow-[0_12px_30px_-10px_rgba(28,30,38,0.6)]' : 'bg-paper text-ink hover:shadow-[0_12px_30px_-10px_rgba(242,183,5,0.5)]'
      }`}
    >
      <Github className="size-4" />
      Ver en GitHub
      <span
        className={`grid size-8 place-items-center rounded-full transition-transform duration-300 group-hover:rotate-45 ${
          dark ? 'bg-myna text-ink' : 'bg-ink text-paper'
        }`}
      >
        <ArrowUpRight className="size-4" />
      </span>
    </a>
  )
}

export default function App() {
  return (
    <div className="relative overflow-x-clip">
      {/* Nav */}
      <header className="sticky top-0 z-20 border-b border-ink/5 bg-paper/75 backdrop-blur-xl">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-8">
          <a href="#" className="flex items-center gap-2 text-[15px] font-semibold tracking-tight">
            <img src={LOGO} alt="" className="size-9" />
            Myna <span className="font-mono text-xs font-normal text-ink/50">STT</span>
          </a>
          <div className="flex items-center gap-1 text-sm text-ink/70">
            <a href="#como-funciona" className="hidden rounded-full px-4 py-2 transition hover:bg-ink/5 hover:text-ink sm:block">
              Cómo funciona
            </a>
            <a href="#caracteristicas" className="hidden rounded-full px-4 py-2 transition hover:bg-ink/5 hover:text-ink sm:block">
              Características
            </a>
            <a
              href={GITHUB}
              target="_blank"
              rel="noreferrer"
              className="ml-2 inline-flex items-center gap-2 rounded-full border border-ink/15 px-4 py-2 font-medium text-ink transition hover:bg-ink hover:text-paper"
            >
              <Github className="size-4" />
              GitHub
            </a>
          </div>
        </nav>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-5 pb-16 pt-6 sm:gap-14 sm:px-8 sm:pb-24 sm:pt-10 lg:grid-cols-[1.1fr_1fr] lg:pt-12">
          <div className="rise">
            <span className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/60 py-1 pl-1 pr-3 text-xs font-medium text-ink/70">
              <span className="rounded-full bg-myna px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-ink">
                Open source
              </span>
              Voz local · Síntesis con IA
            </span>
            <h1 className="mt-5 text-[clamp(3.25rem,13vw,6.25rem)] sm:mt-7 font-semibold leading-[0.92] tracking-[-0.055em]">
              Tu voz,
              <br />
              <span className="font-serif text-[1.08em] font-normal italic tracking-[-0.03em] text-bark">otra voz.</span>
            </h1>
            <p className="mt-5 max-w-md text-base leading-relaxed sm:mt-7 sm:text-lg text-ink/60">
              Habla con tu micrófono y deja que otra voz lo diga por ti. Whisper te escucha en local y Fish Audio
              pone la voz que elijas.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-3 sm:mt-9">
              <GithubButton />
              <a
                href="#como-funciona"
                className="inline-flex h-12 items-center rounded-full px-5 text-[15px] font-medium text-ink/70 transition hover:text-ink"
              >
                Cómo funciona →
              </a>
            </div>
          </div>
          <HeroDemo />
        </section>

        {/* How it works */}
        <section id="como-funciona" className="scroll-mt-20 border-y border-ink/10 bg-white/50">
          <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-24">
            <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.16em] text-bark">Cómo funciona</p>
                <h2 className="mt-3 max-w-lg text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">
                  De tu boca <span className="font-serif font-normal italic text-ink/50">a otra voz.</span>
                </h2>
              </div>
              <p className="max-w-xs text-ink/60">Funciona como un push-to-talk: hablas, sueltas y una voz de IA lo dice por ti.</p>
            </div>

            <ol className="mt-10 grid gap-px sm:mt-14 overflow-hidden rounded-3xl border border-ink/10 bg-ink/10 sm:grid-cols-2 lg:grid-cols-4">
              {steps.map(({ n, icon: Icon, title, text }) => (
                <li key={n} className="group relative bg-paper p-6 transition-colors sm:p-8 duration-300 hover:bg-white">
                  <div className="flex items-center justify-between">
                    <span className="grid size-11 place-items-center rounded-2xl bg-ink text-myna transition-transform duration-300 group-hover:-rotate-6">
                      <Icon className="size-5" />
                    </span>
                    <span className="font-mono text-sm text-ink/30">{n}</span>
                  </div>
                  <h3 className="mt-8 text-xl font-semibold sm:mt-10 tracking-tight">{title}</h3>
                  <p className="mt-2 leading-relaxed text-ink/60">{text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Features */}
        <section id="caracteristicas" className="mx-auto max-w-6xl scroll-mt-20 px-5 py-16 sm:px-8 sm:py-24">
          <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:gap-12">
            <div className="lg:sticky lg:top-28 lg:self-start">
              <p className="font-mono text-xs uppercase tracking-[0.16em] text-bark">Características</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">
                Pensado para <span className="font-serif font-normal italic">sonar bien</span> y encajar en tu setup.
              </h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              {features.map(({ icon: Icon, title, text }) => (
                <article
                  key={title}
                  className="group rounded-3xl border border-ink/10 bg-white p-6 transition-all sm:p-7 duration-300 hover:-translate-y-1 hover:shadow-[0_24px_50px_-30px_rgba(28,30,38,0.35)]"
                >
                  <span className="grid size-10 place-items-center rounded-xl bg-myna/20 text-bark transition-colors group-hover:bg-myna group-hover:text-ink">
                    <Icon className="size-5" />
                  </span>
                  <h3 className="mt-6 text-lg font-semibold sm:mt-8 tracking-tight">{title}</h3>
                  <p className="mt-1.5 text-[15px] leading-relaxed text-ink/60">{text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="px-5 pb-10 sm:px-8">
          <div className="relative mx-auto max-w-6xl overflow-hidden rounded-[2rem] bg-ink px-6 py-12 text-paper sm:rounded-[2.5rem] sm:px-14 sm:py-20">
            <div className="absolute -right-24 -top-24 size-96 rounded-full bg-myna/20 blur-3xl" />
            <div className="relative flex flex-col items-start justify-between gap-10 md:flex-row md:items-end">
              <div>
                <Waveform color="bg-myna" />
                <h2 className="mt-6 max-w-xl text-3xl font-semibold tracking-[-0.04em] sm:text-6xl">
                  Dale tu micrófono. <span className="font-serif font-normal italic text-myna">Myna</span> pone la voz.
                </h2>
              </div>
              <GithubButton dark={false} />
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-5 py-8 text-center text-sm sm:py-10 text-ink/50 sm:flex-row sm:px-8">
        <p>Myna STT · 2026</p>
        <p>
          Proyecto creado por{' '}
          <a
            href="https://miketrollyt.github.io/JC"
            className="font-medium text-ink underline decoration-myna decoration-2 underline-offset-4 transition hover:decoration-ink"
          >
            JC
          </a>
        </p>
      </footer>
    </div>
  )
}
