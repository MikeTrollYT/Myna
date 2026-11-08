import collections
import fnmatch
import glob
import io
import json
import math
import os
import queue
import re
import shutil
import sys
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
import webbrowser
import xml.etree.ElementTree as ET

import customtkinter as ctk
import estilos

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk

# ------------------------------- CONSTANTES -------------------------------

# Carpeta del programa (script o .exe) y de los recursos empaquetados (logo.ico)
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    RECURSOS_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RECURSOS_DIR = APP_DIR

# Datos del usuario (ajustes, fotos y modelos): %LOCALAPPDATA%\MynaSTT
DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share"),
    "MynaSTT",
)
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
ICON_PATH = os.path.join(RECURSOS_DIR, "img/logo.ico")
LOGO_SVG_PATH = os.path.join(RECURSOS_DIR, "img/logo.svg")
COVERS_DIR = os.path.join(DATA_DIR, "covers")
COVER_URL = "https://public-platform.r2.fish.audio/cdn-cgi/image/format=webp/coverimage/{}"
DEFAULT_VOICE_LABEL = "Voz por defecto"
DEFAULT_FISH_VOICE_ID = "8d2c17a9b26d4d83888ea67a1ee565b2"
DEFAULTS = {
    "input_device": "",
    "output_device": "",
    "hotkey": "f9",
    "fish_api_key": "",
    "fish_voice_id": "",
    "fish_model": "s2.1-pro-free",
    "voices": [],
    "normalize_loudness": False,   # Normalización de volumen (Fish Audio)
    "normalize_text": False,       # Normalización de texto (Fish Audio)
    "tag_compat": False,           # Modo de compatibilidad de etiquetas (Fish Audio)
    "monitor_enabled": False,      # Autoescucha: oir tambien lo que se genera
    "monitor_device": "",          # Dispositivo de salida para la autoescucha
    "whisper_model": "small",
    "hf_token": "",
    "silence_rms": 0.005,
}
# Nombre del parametro de la API para el "modo de compatibilidad de etiquetas".
# No aparece en la documentacion publica; si lo averiguas (p. ej. en la pestana Red
# de las herramientas de desarrollador de fish.audio), escribelo aqui. Vacio = no se envia.
TAG_COMPAT_PARAM = ""

STOP_PLAY = threading.Event()
WHISPER_MODELS = ["base", "small", "medium", "large-v3-turbo"]
MODELS_DIR = os.path.join(DATA_DIR, "models")   # aqui se guardan los modelos de Whisper
MODEL_REPOS = {                                 # repositorio de Hugging Face de cada modelo
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
}
HF_BASE = "https://huggingface.co"               # cambiar solo para pruebas
MODEL_FILES = ["config.json", "preprocessor_config.json", "model.bin",
               "tokenizer.json", "vocabulary.*"]
BEAM_SIZE = 1          # 1 = mas rapido; 5 = mas preciso
SR = 16000
BLOCK_S = 0.1
BLOCK = int(SR * BLOCK_S)
PAUSE_CUT = 0.5        # segundos de silencio para cortar un trozo
MIN_SPEECH = 0.4       # minimo de voz para que un trozo cuente
LOW_RMS = 0.002        # nivel minimo para enviar a Whisper el ultimo trozo al soltar la tecla
MAX_SEGMENT = 15.0     # corte forzado si hablas seguido
PROMPT = "¿Cómo estás? Estoy bien, gracias. Vamos a probarlo: ¿qué opinas? ¡Genial!"


def cargar_fuentes():
    """Registra las fuentes de la carpeta fonts/ (Geist, Geist Mono, Instrument Serif)
    solo para esta app: no se instalan en el sistema. Si no están, se usa la sustituta."""
    for ruta in glob.glob(os.path.join(RECURSOS_DIR, "fonts", "*.[to]tf")):
        try:
            ctk.FontManager.load_font(ruta)
        except Exception:  # noqa: BLE001
            pass


def set_windows_app_identity():
    """Asigna una identidad estable para que Windows agrupe la app correctamente."""
    if os.name != "nt":
        return
    import ctypes

    app_id = "MynaSTT.Desktop"
    result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    if result:
        raise ctypes.WinError(result)


# ------------------------------ CONFIGURACION ------------------------------

def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    cleaned = []
    if isinstance(cfg["voices"], list):
        for v in cfg["voices"]:
            if isinstance(v, dict) and str(v.get("name", "")).strip() and str(v.get("id", "")).strip():
                cleaned.append({"name": str(v["name"]).strip(), "id": str(v["id"]).strip()})
    cfg["voices"] = cleaned
    if not cfg["fish_api_key"]:
        cfg["fish_api_key"] = os.environ.get("FISH_API_KEY", "")
    if not cfg["hf_token"]:
        cfg["hf_token"] = os.environ.get("HF_TOKEN", "")
    # El valor vacío representa la opción especial "Voz por defecto".
    # También migra configuraciones creadas por la versión anterior.
    if cfg["fish_voice_id"] == DEFAULT_FISH_VOICE_ID:
        cfg["fish_voice_id"] = ""
    if cfg["fish_voice_id"] and not any(v["id"] == cfg["fish_voice_id"] for v in cleaned):
        cleaned.append({"name": "Mi voz", "id": cfg["fish_voice_id"]})
    return cfg


def extract_id(text):
    """Acepta el ID suelto o un enlace de fish.audio y devuelve el ID."""
    text = (text or "").strip()
    m = re.search(r"[0-9a-fA-F]{32}", text)
    if m:
        return m.group(0).lower()
    if "/" in text:
        text = text.rstrip("/").split("/")[-1]
    return text


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


# -------------------------------- AUDIO / IA --------------------------------

def list_devices():
    """Devuelve ([(nombre, indice)] de entrada, [(nombre, indice)] de salida).
    En Windows se usa solo la API MME para no repetir cada dispositivo."""
    apis = sd.query_hostapis()
    devs = list(sd.query_devices())
    mme = [i for i, a in enumerate(apis) if "MME" in a["name"]]

    def pick(key):
        res = []
        for i, d in enumerate(devs):
            if d[key] <= 0:
                continue
            if mme and d["hostapi"] not in mme:
                continue
            res.append((d["name"], i))
        return res

    return pick("max_input_channels"), pick("max_output_channels")


# ------------------------------ MODELOS WHISPER ------------------------------

def model_dir(name):
    """Carpeta local (models/faster-whisper-<nombre>) donde vive el modelo."""
    return os.path.join(MODELS_DIR, "faster-whisper-" + name)


def model_ready(name):
    """True si el modelo ya esta completo en disco (no hace falta internet)."""
    d = model_dir(name)
    return (all(os.path.exists(os.path.join(d, f)) for f in ("config.json", "tokenizer.json", "model.bin"))
            and bool(glob.glob(os.path.join(d, "vocabulary.*"))))


def download_model(name, on_progress, cancel=None, log=None, hf_token=""):
    """Descarga el modelo a models/ llamando a on_progress(bytes_hechos, bytes_totales).

    Descarga directa con requests (sin depender de huggingface_hub): cada fichero se baja
    a '<fichero>.part' y se renombra al terminar, asi que si se corta o se cancela, la
    proxima vez continua por donde iba. model.bin va el ultimo (su existencia = modelo completo).
    cancel: funcion que devuelve True para abortar (lanza InterruptedError)."""
    log = log or (lambda m: None)
    repo = MODEL_REPOS.get(name, "Systran/faster-whisper-" + name)
    dest = model_dir(name)
    os.makedirs(dest, exist_ok=True)
    on_progress(0, 0)

    auth_headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
    r = requests.get(f"{HF_BASE}/api/models/{repo}?blobs=true",
                     headers=auth_headers, timeout=30)
    r.raise_for_status()
    files = [(f["rfilename"], int(f.get("size") or 0)) for f in r.json().get("siblings", [])
             if any(fnmatch.fnmatch(f["rfilename"], pat) for pat in MODEL_FILES)]
    files.sort(key=lambda x: x[0] == "model.bin")          # model.bin al final
    if not any(n == "model.bin" for n, _ in files):
        raise RuntimeError(f"El repositorio {repo} no contiene model.bin")
    total = sum(sz for _, sz in files)
    done = 0
    last = [0.0]

    def report(force=False):
        now = time.monotonic()
        if force or now - last[0] >= 0.15:
            last[0] = now
            on_progress(done, total)

    for fname, size in files:
        path = os.path.join(dest, fname)
        if os.path.exists(path) and (not size or os.path.getsize(path) == size):
            done += size
            continue
        part = path + ".part"
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if size and have > size:
            os.remove(part)
            have = 0
        if size > 5_000_000:
            log(f"Descargando {fname} ({size / 1e6:.0f} MB)...")
        if not (size and have == size):
            headers = dict(auth_headers)
            if have:
                headers["Range"] = f"bytes={have}-"
            with requests.get(f"{HF_BASE}/{repo}/resolve/main/{fname}", headers=headers,
                              stream=True, timeout=30) as resp:
                resp.raise_for_status()
                if have and resp.status_code != 206:    # el servidor no admite reanudar
                    have = 0
                with open(part, "ab" if have else "wb") as f:
                    got = have
                    for chunk in resp.iter_content(1 << 20):
                        if cancel and cancel():
                            raise InterruptedError("descarga cancelada")
                        f.write(chunk)
                        got += len(chunk)
                        done_now = done + got
                        if time.monotonic() - last[0] >= 0.15:
                            last[0] = time.monotonic()
                            on_progress(done_now, total)
        os.replace(part, path)
        done += size or os.path.getsize(path)
        report(force=True)
    log(f"Modelo '{name}' guardado en {dest}")


def fix_punct(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = []
    for p in parts:
        if p.endswith("?") and "¿" not in p:
            p = "¿" + p
        if p.endswith("!") and "¡" not in p:
            p = "¡" + p
        out.append(p)
    return " ".join(out)


def ensure_final_period(text):
    """Añade un punto a un texto de prueba si no termina en puntuación final."""
    text = text.strip()
    if text and text[-1] not in ".?!":
        return text + "."
    return text


def transcribe(model, audio, prev=""):
    # Sube el volumen de audios flojos (hasta x30) para que Whisper los entienda
    peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    if peak > 0:
        audio = audio * min(0.9 / peak, 30.0)
    segments, _ = model.transcribe(
        audio,
        language="es",
        beam_size=BEAM_SIZE,
        vad_filter=True,
        condition_on_previous_text=False,
        initial_prompt=(PROMPT + " " + prev).strip(),
    )
    return " ".join(s.text.strip() for s in segments).strip()


def _play_on(data, sr, dev, log):
    try:
        ch = data.shape[1]
        if sd.query_devices(dev)["max_output_channels"] < ch:
            data = data.mean(axis=1, keepdims=True).astype("float32")
            ch = 1
        with sd.OutputStream(samplerate=sr, device=dev, channels=ch, dtype="float32") as st:
            for i in range(0, len(data), 2048):
                if STOP_PLAY.is_set():
                    break
                st.write(data[i:i + 2048])
    except Exception as e:  # noqa: BLE001
        log(f"Error al reproducir en el dispositivo {dev}: {e}")


def play_audio(data, sr, devices, log):
    """Reproduce el mismo audio a la vez en varios dispositivos de salida."""
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    STOP_PLAY.clear()
    threads = [threading.Thread(target=_play_on, args=(data, sr, d, log), daemon=True) for d in devices]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def play_pcm_stream(response, devices, log, sample_rate=44100):
    """Reproduce PCM mono de Fish Audio mientras la respuesta sigue llegando."""
    streams = []
    pending = bytearray()
    try:
        for dev in devices:
            streams.append(sd.OutputStream(
                samplerate=sample_rate,
                device=dev,
                channels=1,
                dtype="float32",
            ))
        STOP_PLAY.clear()
        for stream in streams:
            stream.start()
        for chunk in response.iter_content(chunk_size=4096):
            if STOP_PLAY.is_set():
                break
            pending.extend(chunk)
            sample_bytes = len(pending) - (len(pending) % 2)
            if not sample_bytes:
                continue
            samples = (
                np.frombuffer(pending[:sample_bytes], dtype="<i2")
                .astype("float32")
                .reshape(-1, 1)
                / 32768.0
            )
            del pending[:sample_bytes]
            for stream in streams:
                stream.write(samples)
    except Exception as e:  # noqa: BLE001
        log(f"Error al reproducir el audio en streaming: {e}")
    finally:
        for stream in streams:
            try:
                stream.stop()
                stream.close()
            except Exception as e:  # noqa: BLE001
                log(f"Error al cerrar la salida de audio: {e}")


def speak(text, cfg, out_idx, log):
    if not cfg["fish_api_key"]:
        log("Falta la clave de Fish Audio.")
        return
    headers = {"Authorization": f"Bearer {cfg['fish_api_key']}", "Content-Type": "application/json"}
    if cfg.get("fish_model"):
        headers["model"] = cfg["fish_model"]
    payload = {
        "text": text,
        "format": "pcm",
        "sample_rate": 44100,
        "latency": "balanced",
        "normalize": bool(cfg.get("normalize_text", False)),
        "prosody": {
            "speed": 1,
            "volume": 0,
            "normalize_loudness": bool(cfg.get("normalize_loudness", False)),
        },
    }
    if TAG_COMPAT_PARAM and cfg.get("tag_compat"):
        payload[TAG_COMPAT_PARAM] = True
    reference_id = cfg["fish_voice_id"] or DEFAULT_FISH_VOICE_ID
    payload["reference_id"] = reference_id
    try:
        with requests.post(
            "https://api.fish.audio/v1/tts",
            headers=headers,
            json=payload,
            timeout=60,
            stream=True,
        ) as r:
            if r.status_code != 200:
                log(f"Fish Audio devolvio {r.status_code}: {r.text[:200]}")
                return
            devices = out_idx if isinstance(out_idx, (list, tuple)) else [out_idx]
            play_pcm_stream(r, devices, log)
    except requests.RequestException as e:
        log(f"Error de red con Fish Audio: {e}")


class Recorder:
    def __init__(self, eng, audio_q, work_q):
        self.eng = eng
        self.audio_q = audio_q
        self.work_q = work_q
        self.recording = False
        self.buf = []
        self.speech_s = 0.0
        self.silence_s = 0.0
        self.seg_max = 0.0      # nivel maximo del trozo actual
        self.press_max = 0.0    # nivel maximo de toda la pulsacion
        self.sent = False       # si se ha enviado algun trozo a Whisper en esta pulsacion
        self.preroll = collections.deque(maxlen=3)

    def _reset(self):
        self.buf = []
        self.speech_s = 0.0
        self.silence_s = 0.0
        self.seg_max = 0.0

    def _flush(self, final=False):
        secs = len(self.buf) * BLOCK_S
        # Al soltar la tecla se envia el trozo aunque quede por debajo del umbral,
        # siempre que tenga algo de nivel; el VAD de Whisper decide si hay voz.
        ok = self.speech_s >= MIN_SPEECH or (final and secs >= 0.3 and self.seg_max >= LOW_RMS)
        if self.buf and ok:
            self.work_q.put(("audio", np.concatenate(self.buf)))
            self.sent = True
        self._reset()

    def _process(self, block):
        self.buf.append(block)
        rms = float(np.sqrt(np.mean(block ** 2)))
        self.seg_max = max(self.seg_max, rms)
        self.press_max = max(self.press_max, rms)
        if rms > self.eng.silence_rms:
            self.speech_s += BLOCK_S
            self.silence_s = 0.0
        else:
            self.silence_s += BLOCK_S
        seg_len = len(self.buf) * BLOCK_S
        if (self.silence_s >= PAUSE_CUT and self.speech_s >= MIN_SPEECH) or seg_len >= MAX_SEGMENT:
            self._flush()

    def feed(self, block, pressed):
        if pressed and not self.recording:
            self.recording = True
            self._reset()
            self.press_max = 0.0
            self.sent = False
            for b in self.preroll:
                self._process(b)
            self.preroll.clear()
            self.eng.ui("status", "Grabando...")
        if self.recording:
            if block is not None:
                self._process(block)
            if not pressed:
                while not self.audio_q.empty():
                    self._process(self.audio_q.get_nowait())
                self.recording = False
                self._flush(final=True)
                if not self.sent:
                    self.eng.log(
                        f"Audio descartado: nivel máximo {self.press_max:.4f}, "
                        f"umbral {self.eng.silence_rms:.4f}. Baja la sensibilidad "
                        f"o habla más cerca del micro."
                    )
                self.work_q.put(("end",))
                self.eng.ui("status", "Procesando...")
        elif block is not None:
            self.preroll.append(block)


class Engine:
    def __init__(self, ui_q):
        self.ui_q = ui_q
        self.model = None
        self.model_name = None
        self.silence_rms = DEFAULTS["silence_rms"]
        self.button_down = False
        self.stop_evt = threading.Event()

    def ui(self, kind, value=None):
        self.ui_q.put((kind, value))

    def log(self, text):
        self.ui("log", text)

    def start(self, cfg, in_idx, out_idx):
        self.stop_evt.clear()
        self.silence_rms = cfg["silence_rms"]
        threading.Thread(target=self._run, args=(dict(cfg), in_idx, out_idx), daemon=True).start()

    def stop(self):
        self.stop_evt.set()
        STOP_PLAY.set()
        try:
            sd.stop()
        except Exception:  # noqa: BLE001
            pass

    def _worker(self, work_q, cfg, out_idx):
        texts = []
        while True:
            job = work_q.get()
            if job[0] == "quit":
                break
            if job[0] == "audio":
                try:
                    t = transcribe(self.model, job[1], " ".join(texts)[-200:])
                except Exception as e:  # noqa: BLE001
                    self.log(f"Error de transcripcion: {e}")
                    continue
                if t:
                    texts.append(t)
                    self.log(f"   ... {t}")
            elif job[0] == "end":
                full = fix_punct(" ".join(texts))
                texts = []
                if not full:
                    self.log("(Whisper no devolvió texto)")
                else:
                    self.log(f"TEXTO: {full}")
                    self.ui("status", "Hablando...")
                    speak(full, cfg, out_idx, self.log)
                if not self.stop_evt.is_set():
                    self.ui("status", f"Activo. Mantén pulsada '{cfg['hotkey']}' para hablar.")

    def _run(self, cfg, in_idx, out_idx):
        import keyboard

        audio_q = queue.Queue()
        work_q = queue.Queue()
        try:
            name = cfg["whisper_model"]
            if self.model is None or self.model_name != name:
                if not model_ready(name):
                    self.ui("status", f"Descargando el modelo Whisper '{name}' (solo la primera vez)...")
                    try:
                        download_model(
                            name,
                            lambda n, t: self.ui("download", (n, t)),
                            cancel=self.stop_evt.is_set,
                            log=self.log,
                            hf_token=cfg.get("hf_token", ""),
                        )
                    except InterruptedError:
                        self.log("Descarga cancelada: continuará donde se quedó la próxima vez.")
                        return
                    finally:
                        self.ui("download", None)
                self.ui("status", "Cargando Whisper...")
                from faster_whisper import WhisperModel

                self.model = WhisperModel(model_dir(name), device="cpu", compute_type="int8")
                self.model_name = name
            threading.Thread(target=self._worker, args=(work_q, cfg, out_idx), daemon=True).start()
            rec = Recorder(self, audio_q, work_q)
            self.ui("status", f"Activo. Mantén pulsada '{cfg['hotkey']}' para hablar.")

            def callback(indata, frames, time_info, status):
                audio_q.put(indata[:, 0].copy())

            with sd.InputStream(samplerate=SR, channels=1, dtype="float32",
                                blocksize=BLOCK, device=in_idx, callback=callback):
                while not self.stop_evt.is_set():
                    try:
                        block = audio_q.get(timeout=0.2)
                    except queue.Empty:
                        block = None
                    try:
                        pressed = keyboard.is_pressed(cfg["hotkey"]) or self.button_down
                    except ValueError:
                        self.log(f"Tecla no válida: '{cfg['hotkey']}'. Cámbiala y vuelve a iniciar.")
                        break
                    if block is not None:
                        level = float(np.sqrt(np.mean(block ** 2))) if pressed else 0.0
                        self.ui("level", level)
                    rec.feed(block, pressed)
        except Exception as e:  # noqa: BLE001
            self.log(f"Error: {e}")
        finally:
            work_q.put(("quit",))
            self.ui("status", "Detenido.")
            self.ui("running", False)


# ----------------------------------- GUI -----------------------------------
# Todo el aspecto (colores, fuentes, medidas) vive en estilos.py.

def cargar_logo_svg(size):
    """Convierte el SVG del logo en una imagen PIL para mostrarlo en Tk."""
    root = ET.parse(LOGO_SVG_PATH).getroot()
    render_size = max(size * 8, 256)
    imagen = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(imagen)
    escala = render_size / 512
    for rect in root:
        if rect.tag.rsplit("}", 1)[-1] != "rect":
            continue
        x = float(rect.attrib["x"]) * escala
        y = float(rect.attrib["y"]) * escala
        ancho = float(rect.attrib["width"]) * escala
        alto = float(rect.attrib["height"]) * escala
        radio = float(rect.attrib.get("rx", 0)) * escala
        color = rect.attrib["fill"]
        dibujo.rounded_rectangle(
            (round(x), round(y), round(x + ancho), round(y + alto)),
            radius=round(radio),
            fill=color,
        )
    caja = imagen.getbbox()
    if caja:
        imagen = imagen.crop(caja)
    escala_final = min(size / imagen.width, size / imagen.height)
    destino = (
        max(1, round(imagen.width * escala_final)),
        max(1, round(imagen.height * escala_final)),
    )
    imagen = imagen.resize(destino, Image.Resampling.LANCZOS)
    lienzo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    lienzo.paste(imagen, ((size - imagen.width) // 2, (size - imagen.height) // 2), imagen)
    return lienzo


def crear_cabecera(parent, titulo, acento, subtitulo=None, volver=None, insignia=None, marca=False):
    """Cabecera común de las vistas con marca o título y subtítulo opcionales."""
    barra = ctk.CTkFrame(parent, fg_color=estilos.TRANSPARENTE)
    barra.pack(fill="x", padx=estilos.MARGEN, pady=(estilos.MARGEN, estilos.SEPARACION))
    if volver:
        ctk.CTkButton(barra, text="←  Volver", command=volver,
                      **estilos.boton("secundario", width=100)).pack(side="left", padx=(0, 16))
    acciones = ctk.CTkFrame(barra, fg_color=estilos.TRANSPARENTE, width=0, height=0)
    acciones.pack(side="right")
    textos = ctk.CTkFrame(barra, fg_color=estilos.TRANSPARENTE)
    textos.pack(side="left", fill="x", expand=True)
    if marca:
        logo_size = 54
        logo = ctk.CTkImage(light_image=cargar_logo_svg(logo_size),
                            size=(logo_size, logo_size))
        ctk.CTkLabel(textos, image=logo, text="").pack(side="left", padx=(0, 10))
        ctk.CTkLabel(textos, text="Myna", **estilos.ETIQUETA["titulo"]).pack(
            side="left", anchor="center")
    elif insignia:
        pastilla = ctk.CTkFrame(textos, **estilos.PASTILLA)
        pastilla.pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(pastilla, text=insignia[0], **estilos.INSIGNIA).pack(
            side="left", padx=(3, 8), pady=3)
        ctk.CTkLabel(pastilla, text=insignia[1], **estilos.ETIQUETA["suave"]).pack(
            side="left", padx=(0, 12))
    if not marca:
        fila = ctk.CTkFrame(textos, fg_color=estilos.TRANSPARENTE)
        fila.pack(anchor="w")
        ctk.CTkLabel(fila, text=titulo + (" " if acento else ""), **estilos.ETIQUETA["titulo"]).pack(
            side="left", anchor="s")
        if acento:
            ctk.CTkLabel(fila, text=acento, **estilos.ETIQUETA["titulo_serif"]).pack(
                side="left", anchor="s")
    if subtitulo:
        ctk.CTkLabel(textos, text=subtitulo, **estilos.ETIQUETA["subtitulo"]).pack(
            anchor="w", pady=(2, 0))
    return acciones


# ------------------------ TARJETA CENTRAL (ONDA DE VOZ) ------------------------
# Todo se dibuja a mano: el fondo (sombra, resplandor, puntitos, píldora) con PIL a doble
# resolución para que los bordes salgan suaves, y la onda, el medidor y el micrófono encima.

ESTADOS_PANEL = (   # (texto de estado que envía el motor, etiqueta corta, modo)
    ("Grabando", "GRABANDO", "grabando"),
    ("Detenido", "DETENIDO", "off"),
    ("Activo", "LISTO", "listo"),
    ("Procesando", "PROCESANDO", "ocupado"),
    ("Hablando", "HABLANDO", "ocupado"),
    ("Cargando", "CARGANDO", "ocupado"),
    ("Descargando", "DESCARGANDO", "ocupado"),
)
COLOR_PUNTO = {"off": "#C9C2B2", "listo": estilos.PRIMARIO,
               "grabando": estilos.PELIGRO, "ocupado": estilos.ACENTO}


def _rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _pos_nivel(x):
    """Nivel RMS (0-0.05) -> fracción 0-1 con escala de raíz, igual que el medidor de siempre."""
    return min((max(float(x), 0.0) / 0.05) ** 0.5, 1.0)


def _escala(widget):
    return ctk.ScalingTracker.get_window_scaling(widget)


def geometria_panel(w, h, esc):
    """Posiciones (en píxeles) de la tarjeta, la píldora del micro y la zona de la onda."""
    mx, arriba, abajo = 14 * esc, 6 * esc, 30 * esc
    x0, y0, x1, y1 = mx, arriba, w - mx, h - abajo
    alto_p, margen_p = 58 * esc, 18 * esc
    py1 = y1 - margen_p
    py0 = py1 - alto_p
    return {
        "x0": x0, "y0": y0, "x1": x1, "y1": y1,
        "px0": x0 + margen_p, "px1": x1 - margen_p,
        "py0": py0, "py1": py1, "pyc": (py0 + py1) / 2, "alto_p": alto_p,
        "wy0": y0 + 52 * esc, "wy1": py0 - 14 * esc,
    }


def pil_fondo_panel(w, h, esc, activo):
    """Imagen de fondo de la tarjeta: sombra, tarjeta, resplandor amarillo, puntitos y píldora."""
    g = geometria_panel(w, h, esc)
    ss = 2

    def s(v):
        return int(round(v * ss))

    W, H = w * ss, h * ss
    caja = (s(g["x0"]), s(g["y0"]), s(g["x1"]), s(g["y1"]))
    radio = s(30 * esc)

    base = Image.new("RGB", (W, H), _rgb(estilos.FONDO))
    sombra = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sombra).rounded_rectangle(
        (caja[0] + s(14 * esc), caja[1] + s(14 * esc), caja[2] - s(14 * esc), caja[3] + s(8 * esc)),
        radius=radio, fill=80)
    sombra = sombra.filter(ImageFilter.GaussianBlur(s(10 * esc)))
    base.paste(Image.new("RGB", (W, H), _rgb(estilos.ACENTO)), mask=sombra)

    tarjeta = Image.new("RGB", (W, H), _rgb(estilos.PANEL))
    cx = (caja[0] + caja[2]) / 2
    cy = s((g["wy0"] + g["wy1"]) / 2)
    rx = (caja[2] - caja[0]) * (0.46 if activo else 0.36)
    ry = s((g["wy1"] - g["wy0"]) / 2) * (1.9 if activo else 1.5)
    yy, xx = np.ogrid[0:H, 0:W]
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    a = np.clip(1 - d, 0, 1) ** 1.8 * (0.8 if activo else 0.55)
    arr = np.asarray(tarjeta, dtype=np.float32)
    glow = np.array(_rgb("#F7CE4A"), dtype=np.float32)
    arr = arr * (1 - a[..., None]) + glow * a[..., None]
    tarjeta = Image.fromarray(arr.astype(np.uint8))

    puntos = Image.new("L", (W, H), 0)
    dp = ImageDraw.Draw(puntos)
    paso = s(22 * esc)
    r = max(1, s(0.9 * esc))
    for y in range(caja[1] + paso // 2, caja[3], paso):
        for x in range(caja[0] + paso // 2, caja[2], paso):
            dp.ellipse((x - r, y - r, x + r, y + r), fill=30)
    tarjeta.paste(Image.new("RGB", (W, H), _rgb(estilos.TEXTO)), mask=puntos)

    pildora = (s(g["px0"]), s(g["py0"]), s(g["px1"]), s(g["py1"]))
    ImageDraw.Draw(tarjeta).rounded_rectangle(
        pildora, radius=(pildora[3] - pildora[1]) // 2, fill=_rgb(estilos.ENTRADA),
        outline=_rgb(estilos.BORDES), width=ss)

    mascara = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mascara).rounded_rectangle(caja, radius=radio, fill=255)
    base.paste(tarjeta, mask=mascara)
    ImageDraw.Draw(base).rounded_rectangle(caja, radius=radio, outline=_rgb(estilos.BORDES), width=ss)
    return base.resize((w, h), Image.LANCZOS)


def pil_microfono(d, color_fondo, color_icono):
    """Círculo con un micrófono dentro (RGBA, suavizado)."""
    ss = 4
    D = d * ss
    img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.ellipse((0, 0, D - 1, D - 1), fill=_rgb(color_fondo))
    ic = _rgb(color_icono)
    ancho = max(2, int(D * 0.065))
    dr.rounded_rectangle((int(D * 0.42), int(D * 0.24), int(D * 0.58), int(D * 0.55)),
                         radius=int(D * 0.08), fill=ic)
    dr.arc((int(D * 0.33), int(D * 0.36), int(D * 0.67), int(D * 0.66)), 0, 180, fill=ic, width=ancho)
    dr.line((int(D * 0.5), int(D * 0.66), int(D * 0.5), int(D * 0.74)), fill=ic, width=ancho)
    dr.line((int(D * 0.41), int(D * 0.74), int(D * 0.59), int(D * 0.74)), fill=ic, width=ancho)
    return img.resize((d, d), Image.LANCZOS)


def dibujar_medidor(canvas, val, thr, esc, segmentos=24):
    """Medidor de nivel a segmentos: se enciende hasta `val`; el segmento oscuro marca el umbral."""
    m = estilos.MEDIDOR
    w = max(canvas.winfo_width(), 60)
    h = max(canvas.winfo_height(), 10)
    canvas.delete("all")
    zona = max(w - 56 * esc, 40)
    paso = zona / segmentos
    grosor = max(2, round(min(paso * 0.5, 4 * esc)))
    lleno = int(round(_pos_nivel(val) * segmentos))
    marca = min(segmentos - 1, int(_pos_nivel(thr) * segmentos))
    activo = val > thr
    for i in range(segmentos):
        x = (i + 0.5) * paso
        mitad = min((3 + 6 * i / (segmentos - 1)) * esc, h / 2 - 1)
        if i == marca:
            color = m["umbral"]
        elif i < lleno:
            color = m["barra_activa"] if activo else m["barra_baja"]
        else:
            color = m["barra_inactiva"]
        canvas.create_line(x, h / 2 - mitad, x, h / 2 + mitad, width=grosor,
                           capstyle="round", fill=color)
    canvas.create_text(w - 2, h / 2, anchor="e", font=(estilos.FUENTE_MONO, -round(11 * esc)),
                       fill=m["texto"], text=f"{val:.3f}")


class PanelVoz(tk.Canvas):
    """Tarjeta principal: estado, onda de voz animada y botón de hablar (el micrófono)."""

    ALTO = 280
    BARRAS = 37
    SEGMENTOS = 22

    def __init__(self, parent, app):
        self.app = app
        self.esc = _escala(app)
        super().__init__(parent, bg=estilos.FONDO, highlightthickness=0, bd=0,
                         height=int(self.ALTO * self.esc))
        self.modo = "off"            # off | listo | grabando | ocupado
        self.etiqueta = "DETENIDO"
        self.t = 0.0
        self.ticks = 0
        self.nivel = 0.0
        self.hist = collections.deque([0.0] * self.BARRAS, maxlen=self.BARRAS)
        self._tam = None
        self._imgs = {}
        self._items = {}
        self._barras, self._bx = [], []
        self._segs = []
        self._resize_job = None
        self.bind("<Configure>", self._on_configure)
        self.bind("<ButtonRelease-1>", self._soltar)
        self.after(100, self._tick)

    # ---- construcción ----
    def _on_configure(self, _event):
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, self._construir)

    def _construir(self):
        self._resize_job = None
        w, h = self.winfo_width(), self.winfo_height()
        if w < 200 or h < 100 or (w, h) == self._tam:
            return
        self._tam = (w, h)
        esc = self.esc = _escala(self.app)
        g = geometria_panel(w, h, esc)
        d = int(round(g["alto_p"] - 12 * esc))
        colores_mic = {"off": ("#C9C2B2", estilos.PANEL), "listo": (estilos.TEXTO, estilos.FONDO),
                       "grabando": (estilos.PRIMARIO, estilos.TEXTO)}
        self._imgs = {
            "fondo": {a: ImageTk.PhotoImage(pil_fondo_panel(w, h, esc, a), master=self)
                      for a in (False, True)},
            "mic": {k: ImageTk.PhotoImage(pil_microfono(d, *c), master=self)
                    for k, c in colores_mic.items()},
        }
        self.delete("all")
        self._items = {}
        self.create_image(0, 0, anchor="nw", image=self._imgs["fondo"][False], tags="fondo")

        # Cabecera de la tarjeta: punto de estado + etiquetas en mono
        fm = (estilos.FUENTE_MONO, -round(11 * esc))
        yh = g["y0"] + 28 * esc
        xp = g["x0"] + 30 * esc
        r = 4 * esc
        self._items["punto"] = self.create_oval(xp - r, yh - r, xp + r, yh + r,
                                                fill=COLOR_PUNTO["off"], outline="")
        self._items["estado"] = self.create_text(xp + 14 * esc, yh, anchor="w", text=self.etiqueta,
                                                 font=fm, fill=estilos.TEXTO_MICRO)
        self.create_text(g["x1"] - 30 * esc, yh, anchor="e", text="MYNA · LOCAL",
                         font=fm, fill=estilos.TEXTO_MICRO)

        # Onda de voz
        n = self.BARRAS
        wx0, wx1 = g["x0"] + 70 * esc, g["x1"] - 70 * esc
        paso = (wx1 - wx0) / (n - 1)
        self._ancho_barra = max(3, round(min(7 * esc, paso * 0.55)))
        self._yc = (g["wy0"] + g["wy1"]) / 2
        self._amp = max((g["wy1"] - g["wy0"]) / 2 - self._ancho_barra / 2, 4)
        self._bx = [wx0 + i * paso for i in range(n)]
        self._barras = [
            self.create_line(x, self._yc - 1, x, self._yc + 1, width=self._ancho_barra,
                             capstyle="round", fill=estilos.ACENTO)
            for x in self._bx]

        # Píldora inferior: micrófono, texto y medidor
        self._rr = d / 2
        self._mx = g["px0"] + g["alto_p"] / 2
        self._my = g["pyc"]
        self._items["anillo"] = self.create_oval(
            self._mx - self._rr, self._my - self._rr, self._mx + self._rr, self._my + self._rr,
            outline=estilos.PRIMARIO, width=max(2, round(2 * esc)), state="hidden")
        self._items["mic"] = self.create_image(self._mx, self._my, image=self._imgs["mic"]["off"],
                                               tags="mic")
        self.tag_bind("mic", "<ButtonPress-1>", self._pulsar)
        self.tag_bind("mic", "<Enter>", lambda _e: self.configure(cursor="hand2"))
        self.tag_bind("mic", "<Leave>", lambda _e: self.configure(cursor=""))
        self._items["texto"] = self.create_text(
            self._mx + self._rr + 16 * esc, self._my, anchor="w", text="",
            font=(estilos.FUENTE, -round(13 * esc)), fill="#9A968A")

        ns = self.SEGMENTOS
        mw = min(170 * esc, (g["px1"] - g["px0"]) * 0.3)
        mx1 = g["px1"] - 28 * esc
        pas = mw / ns
        grosor = max(2, round(min(3.2 * esc, pas * 0.55)))
        self._segs = []
        for i in range(ns):
            x = mx1 - mw + (i + 0.5) * pas
            mitad = (3 + 7 * i / (ns - 1)) * esc
            self._segs.append(self.create_line(x, self._my - mitad, x, self._my + mitad,
                                               width=grosor, capstyle="round",
                                               fill=estilos.MEDIDOR["barra_inactiva"]))
        self._aplicar_modo()
        self._animar()

    # ---- estado ----
    def set_estado(self, texto):
        etiqueta, modo = "EN CURSO", "ocupado"
        for prefijo, etq, mod in ESTADOS_PANEL:
            if texto.startswith(prefijo):
                etiqueta, modo = etq, mod
                break
        self.etiqueta, self.modo = etiqueta, modo
        self._aplicar_modo()

    def actualizar_texto(self):
        if "texto" not in self._items:
            return
        tecla = self.app.key_var.get().upper()
        textos = {
            "off": "Pulsa Iniciar para empezar",
            "listo": f"Mantén pulsado el micro o {tecla}",
            "grabando": "Escuchando…",
            "ocupado": self.etiqueta.capitalize() + "…",
        }
        self.itemconfigure(self._items["texto"], text=textos[self.modo],
                           fill=estilos.TEXTO if self.modo == "grabando" else "#9A968A")

    def _aplicar_modo(self):
        if not self._items:
            return
        self.itemconfigure(self._items["punto"], fill=COLOR_PUNTO[self.modo])
        self.itemconfigure(self._items["estado"], text=self.etiqueta)
        self.itemconfigure("fondo", image=self._imgs["fondo"][self.modo == "grabando"])
        clave = "off" if self.modo == "off" else "grabando" if self.modo == "grabando" else "listo"
        self.itemconfigure(self._items["mic"], image=self._imgs["mic"][clave])
        self.actualizar_texto()

    # ---- botón de hablar ----
    def _pulsar(self, _event):
        self.app.engine.button_down = True

    def _soltar(self, _event):
        self.app.engine.button_down = False

    # ---- animación ----
    def _tick(self):
        activa = bool(self._tam and self._items and self.winfo_ismapped())
        try:
            self.after(33 if activa else 250, self._tick)
        except tk.TclError:
            return
        if activa:
            self._animar()

    def _animar(self):
        app = self.app
        self.t += 0.033
        self.ticks += 1
        thr = _pos_nivel(app.thr_var.get())
        objetivo = _pos_nivel(app.last_level) if app.running else 0.0
        self.nivel += (objetivo - self.nivel) * (0.6 if objetivo > self.nivel else 0.2)
        if self.ticks % 2 == 0:
            self.hist.append(self.nivel)

        n = self.BARRAS
        for i, (item, x, v) in enumerate(zip(self._barras, self._bx, self.hist)):
            env = 0.4 + 0.6 * math.sin(math.pi * (i + 0.5) / n)
            mitad = max(v * env * self._amp, 0.6)
            if i >= n - 3:
                color = estilos.PRIMARIO
            elif v >= thr:
                color = estilos.TEXTO
            else:
                color = estilos.ACENTO
            self.coords(item, x, self._yc - mitad, x, self._yc + mitad)
            self.itemconfigure(item, fill=color)

        m = estilos.MEDIDOR
        ns = self.SEGMENTOS
        lleno = int(round(self.nivel * ns))
        marca = min(ns - 1, int(thr * ns))
        activo = self.nivel > thr
        for i, seg in enumerate(self._segs):
            if i == marca:
                color = m["umbral"]
            elif i < lleno:
                color = m["barra_activa"] if activo else m["barra_baja"]
            else:
                color = m["barra_inactiva"]
            self.itemconfigure(seg, fill=color)

        anillo = self._items["anillo"]
        if self.modo == "grabando":
            r = self._rr * (1.10 + 0.10 * math.sin(self.t * 6))
            self.coords(anillo, self._mx - r, self._my - r, self._mx + r, self._my + r)
            self.itemconfigure(anillo, state="normal")
        else:
            self.itemconfigure(anillo, state="hidden")


class SmoothScrollableFrame(ctk.CTkScrollableFrame):
    """Contenedor que agrupa la rueda para evitar repintados parciales del canvas."""

    WHEEL_UNITS = 26
    MAX_FRAME_UNITS = 10

    def __init__(self, *args, **kwargs):
        self._pending_scroll_x = 0.0
        self._pending_scroll_y = 0.0
        self._scroll_job = None
        super().__init__(*args, **kwargs)

    def _mouse_wheel_all(self, event):
        if not self._check_if_valid_scroll(event.widget):
            return
        if not sys.platform.startswith("win"):
            super()._mouse_wheel_all(event)
            return

        delta = getattr(event, "delta", 0)
        if not delta:
            delta = 120 if getattr(event, "num", 4) == 4 else -120
        # Un giro de rueda de Windows equivale normalmente a 120; 20 unidades
        # dejan un desplazamiento cómodo sin obligar a repetir tantos giros.
        steps = -(delta / 120) * self.WHEEL_UNITS
        if self._shift_pressed:
            self._pending_scroll_x += steps
        else:
            self._pending_scroll_y += steps
        if self._scroll_job is None:
            self._scroll_job = self.after(16, self._flush_scroll)

    def _flush_scroll(self):
        self._scroll_job = None
        max_steps = self.MAX_FRAME_UNITS
        x_steps = max(-max_steps, min(max_steps, int(self._pending_scroll_x)))
        y_steps = max(-max_steps, min(max_steps, int(self._pending_scroll_y)))
        self._pending_scroll_x -= x_steps
        self._pending_scroll_y -= y_steps
        if x_steps:
            self._parent_canvas.xview_scroll(x_steps, "units")
        if y_steps:
            self._parent_canvas.yview_scroll(y_steps, "units")
        if abs(self._pending_scroll_x) >= 1 or abs(self._pending_scroll_y) >= 1:
            self._scroll_job = self.after(16, self._flush_scroll)


class VoiceLibrary(ctk.CTkFrame):
    """Vista de la biblioteca: lista de voces con foto, donde se elige la voz activa."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=estilos.FONDO)
        self.app = app
        acciones = crear_cabecera(self, "Biblioteca de", "voces.",
                                  "Elige la voz que usará la app o añade una nueva.",
                                  volver=app.show_main)
        self.add_button = ctk.CTkButton(acciones, text="+  Añadir voz", command=self.show_form,
                                        **estilos.boton("primario", width=132))
        self.add_button.pack()

        self.list_frame = SmoothScrollableFrame(self, **estilos.SCROLL)
        self.grid_host = ctk.CTkFrame(self.list_frame, fg_color=estilos.TRANSPARENTE)
        self.grid_host.pack(fill="x")
        self._cards = []
        self._cols = 0
        self._resize_job = None
        self.bind("<Configure>", self._on_resize)
        self.form_frame = ctk.CTkFrame(self, fg_color=estilos.TRANSPARENTE)
        self._build_form()
        self.show_list()

    # ---- lista ----
    def show_list(self):
        self.form_frame.pack_forget()
        self.add_button.configure(state="normal")
        self.list_frame.pack(fill="both", expand=True,
                             padx=estilos.MARGEN - 6, pady=(0, estilos.MARGEN - 6))
        self.render()

    def render(self):
        for w in self.grid_host.winfo_children():
            w.destroy()
        for w in self.list_frame.winfo_children():
            if w is not self.grid_host:
                w.destroy()
        self._cards = []
        self._cols = 0
        current = self.app.cfg["fish_voice_id"]
        self._card("", DEFAULT_VOICE_LABEL, "Sin voz personalizada", current == "", removable=False)
        for v in self.app.cfg["voices"]:
            self._card(v["id"], v["name"], v["id"], v["id"] == current, removable=True)
        self._reflow(force=True)
        if not self.app.cfg["voices"]:
            ctk.CTkLabel(self.list_frame, text="Aún no has añadido voces propias",
                         **estilos.ETIQUETA["vacio"]).pack(pady=(20, 4))
            ctk.CTkLabel(self.list_frame, text="Pulsa «Añadir voz» para guardar la primera.",
                         **estilos.ETIQUETA["suave"]).pack()

    # ---- rejilla adaptable ----
    def _on_resize(self, event=None):
        # Ojo: en CustomTkinter bind() se engancha al canvas interno, por eso no se filtra event.widget.
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(60, self._reflow)

    def _columnas(self):
        ancho = self.winfo_width() - 2 * (estilos.MARGEN - 6) - 24  # 24 = barra de scroll
        celda = estilos.TARJETA_VOZ_ANCHO + 2 * estilos.TARJETA_VOZ_GAP
        return max(1, ancho // celda)

    def _reflow(self, force=False):
        """Reparte los cuadritos en filas según el ancho disponible."""
        self._resize_job = None
        cols = self._columnas()
        if cols == self._cols and not force:
            return
        for c in range(max(self._cols, cols)):
            self.grid_host.grid_columnconfigure(c, weight=1 if c < cols else 0)
        gap = estilos.TARJETA_VOZ_GAP
        for i, card in enumerate(self._cards):
            card.grid(row=i // cols, column=i % cols, padx=gap, pady=gap)
        self._cols = cols

    @staticmethod
    def _recortar(texto, maximo):
        return texto if len(texto) <= maximo else texto[:maximo - 1] + "…"

    def _card(self, vid, name, sub, active, removable):
        card = ctk.CTkFrame(self.grid_host, width=estilos.TARJETA_VOZ_ANCHO,
                            height=estilos.TARJETA_VOZ_ALTO,
                            **(estilos.TARJETA_ACTIVA if active else estilos.TARJETA))
        card.pack_propagate(False)
        self._cards.append(card)

        # Botones abajo (se empaquetan primero para que siempre queden visibles)
        botones = ctk.CTkFrame(card, fg_color=estilos.TRANSPARENTE)
        botones.pack(side="bottom", fill="x", padx=14, pady=(0, 14))
        if removable:
            ctk.CTkButton(botones, text="✕", command=lambda i=vid: self.remove(i),
                          **estilos.boton("peligro_suave", width=36)).pack(side="right", padx=(8, 0))
        if active:
            ctk.CTkLabel(botones, text="●  EN USO", **estilos.INSIGNIA).pack(
                side="left", fill="x", expand=True, ipady=4)
        else:
            ctk.CTkButton(botones, text="Usar", command=lambda i=vid: self.use(i),
                          **estilos.boton("primario")).pack(side="left", fill="x", expand=True)

        self.app.make_avatar(card, vid, name, estilos.AVATAR_BIBLIOTECA).pack(pady=(16, 8))
        ctk.CTkLabel(card, text=self._recortar(name, 18),
                     **estilos.ETIQUETA["nombre_cuadro"]).pack(fill="x", padx=10)
        sub_txt = sub if len(sub) <= 18 else sub[:8] + "…" + sub[-6:]
        ctk.CTkLabel(card, text=sub_txt, **estilos.ETIQUETA["suave_centro"]).pack(
            fill="x", padx=10, pady=(2, 0))

    def use(self, vid):
        if self.app.running:
            self.app.show_modal("Voz", "Pulsa Detener en la ventana principal para cambiar de voz.")
            return
        self.app.select_voice(vid)
        self.render()

    def remove(self, vid):
        cfg = self.app.cfg
        if self.app.running and vid == cfg["fish_voice_id"]:
            self.app.show_modal("Voz", "Pulsa Detener antes de eliminar la voz en uso.")
            return
        self.app.show_modal(
            "Eliminar voz",
            "¿Eliminar esta voz de la biblioteca?",
            buttons=(
                ("Cancelar", "secundario", None),
                ("Eliminar", "peligro", lambda: self._confirm_remove(vid)),
            ),
        )

    def _confirm_remove(self, vid):
        cfg = self.app.cfg
        cfg["voices"] = [v for v in cfg["voices"] if v["id"] != vid]
        if cfg["fish_voice_id"] == vid:
            cfg["fish_voice_id"] = ""
        save_config(cfg)
        self.app.refresh_voice_card()
        self.render()

    # ---- formulario "añadir voz" ----
    def _build_form(self):
        card = ctk.CTkFrame(self.form_frame, **estilos.TARJETA)
        card.pack(fill="x", padx=estilos.MARGEN, pady=(0, estilos.MARGEN))
        pad = estilos.PAD_TARJETA + 6
        ctk.CTkLabel(card, text="Añadir una voz", **estilos.ETIQUETA["seccion"]).pack(
            anchor="w", padx=pad, pady=(pad, 2))
        ctk.CTkLabel(card, text="Guarda una voz de Fish Audio para usarla cuando quieras.",
                     **estilos.ETIQUETA["suave"]).pack(anchor="w", padx=pad, pady=(0, 18))

        self.name_var = tk.StringVar()
        self.id_var = tk.StringVar()
        ctk.CTkLabel(card, text="Nombre visible", **estilos.ETIQUETA["cuerpo"]).pack(
            anchor="w", padx=pad, pady=(0, 4))
        self.name_entry = ctk.CTkEntry(card, textvariable=self.name_var,
                                       placeholder_text="Por ejemplo: Narrador", **estilos.ENTRADA_TEXTO)
        self.name_entry.pack(fill="x", padx=pad, pady=(0, 16))
        ctk.CTkLabel(card, text="ID o enlace de Fish Audio", **estilos.ETIQUETA["cuerpo"]).pack(
            anchor="w", padx=pad, pady=(0, 4))
        ctk.CTkEntry(card, textvariable=self.id_var,
                     placeholder_text="Pega aquí el ID o el enlace de la voz",
                     **estilos.ENTRADA_TEXTO).pack(fill="x", padx=pad, pady=(0, 22))

        btns = ctk.CTkFrame(card, fg_color=estilos.TRANSPARENTE)
        btns.pack(anchor="e", padx=pad, pady=(0, pad))
        ctk.CTkButton(btns, text="Cancelar", command=self.show_list,
                      **estilos.boton("secundario", width=110)).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="Guardar voz", command=self._save_form,
                      **estilos.boton("primario", width=130)).pack(side="left")

    def show_form(self):
        self.name_var.set("")
        self.id_var.set("")
        self.list_frame.pack_forget()
        self.add_button.configure(state="disabled")
        self.form_frame.pack(fill="both", expand=True)
        self.name_entry.focus_set()

    def _save_form(self):
        name = self.name_var.get().strip()
        vid = extract_id(self.id_var.get())
        voices = self.app.cfg["voices"]
        if not name or not vid:
            self.app.show_modal("Añadir voz", "Escribe un nombre y un ID.")
            return
        if any(v["id"] == vid for v in voices):
            self.app.show_modal("Añadir voz", "Esa voz ya está en la biblioteca.")
            return
        if any(v["name"].lower() == name.lower() for v in voices) or name == DEFAULT_VOICE_LABEL:
            self.app.show_modal("Añadir voz", "Ya existe una voz con ese nombre.")
            return
        voices.append({"name": name, "id": vid})
        save_config(self.app.cfg)
        self.app.refresh_voice_card()
        self.show_list()


class App(ctk.CTk):
    def __init__(self):
        set_windows_app_identity()
        super().__init__()
        self.title("Myna STT")
        self.iconbitmap(ICON_PATH)
        self.iconbitmap(default=ICON_PATH)
        self.geometry("820x900")
        self.minsize(740, 780)
        estilos.aplicar(self)
        self.cfg = load_config()
        self.ui_q = queue.Queue()
        self.engine = Engine(self.ui_q)
        self.running = False
        self.controls = []          # widgets de Configuración que se bloquean mientras corre
        self.meters = []            # canvas de los medidores de nivel
        self.last_level = 0.0
        self.covers = {}            # id de voz -> imagen PIL redondeada
        self._cover_cache = {}      # (id, tamaño) -> CTkImage
        self.cover_pending = set()
        self.cover_failed = set()
        device_error = None
        try:
            self.inputs, self.outputs = list_devices()
        except Exception as e:  # noqa: BLE001
            self.inputs, self.outputs = [], []
            device_error = f"No se pudieron listar los dispositivos: {e}"
        self._build()
        if device_error:
            self.after_idle(lambda: self.show_modal("Audio", device_error))
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self.poll)

    # ---- utilidades ----
    def _select(self, items, saved, prefer=None, default_idx=None):
        names = [n for n, _ in items]
        if saved in names:
            return saved
        if prefer:
            for n in names:
                if prefer in n.lower():
                    return n
        if default_idx is not None:
            for n, i in items:
                if i == default_idx:
                    return n
        return names[0] if names else ""

    def _default_in(self):
        try:
            return sd.default.device[0]
        except Exception:  # noqa: BLE001
            return None

    def _default_out(self):
        try:
            return sd.default.device[1]
        except Exception:  # noqa: BLE001
            return None

    def collect_cfg(self):
        # fish_voice_id no se toca aquí: se cambia desde la biblioteca (select_voice)
        self.cfg.update({
            "input_device": self.in_var.get(),
            "output_device": self.out_var.get(),
            "hotkey": self.key_var.get().strip() or "f9",
            "fish_api_key": self.api_var.get().strip(),
            "fish_model": self.fishmodel_var.get().strip(),
            "normalize_loudness": bool(self.normvol_var.get()),
            "normalize_text": bool(self.normtext_var.get()),
            "tag_compat": bool(self.tagcompat_var.get()),
            "monitor_enabled": bool(self.monitor_var.get()),
            "monitor_device": self.mondev_var.get(),
            "whisper_model": self.model_var.get(),
            "hf_token": self.hf_token_var.get().strip(),
            "silence_rms": round(float(self.thr_var.get()), 4),
        })

    # ---- construcción ----
    def _init_vars(self):
        self.in_var = tk.StringVar(value=self._select(
            self.inputs, self.cfg["input_device"], default_idx=self._default_in()))
        self.out_var = tk.StringVar(value=self._select(
            self.outputs, self.cfg["output_device"], prefer="cable input", default_idx=self._default_out()))
        self.key_var = tk.StringVar(value=self.cfg["hotkey"])
        self.api_var = tk.StringVar(value=self.cfg["fish_api_key"])
        self.fishmodel_var = tk.StringVar(value=self.cfg["fish_model"])
        self.model_var = tk.StringVar(value=self.cfg["whisper_model"])
        self.hf_token_var = tk.StringVar(value=self.cfg["hf_token"])
        self.thr_var = tk.DoubleVar(value=self.cfg["silence_rms"])
        self.normvol_var = tk.BooleanVar(value=bool(self.cfg["normalize_loudness"]))
        self.normtext_var = tk.BooleanVar(value=bool(self.cfg["normalize_text"]))
        self.tagcompat_var = tk.BooleanVar(value=bool(self.cfg["tag_compat"]))
        self.monitor_var = tk.BooleanVar(value=bool(self.cfg["monitor_enabled"]))
        self.mondev_var = tk.StringVar(value=self._select(
            self.outputs, self.cfg["monitor_device"], default_idx=self._default_out()))
        self.status_var = tk.StringVar(value="Detenido.")
        self.test_var = tk.StringVar(value="Hola, esto es una prueba.")
        self.key_var.trace_add("write", lambda *_: self._update_hotkey_hint())

    def show_modal(self, title, message, buttons=None):
        """Muestra un aviso modal integrado sobre la vista actual."""
        if hasattr(self, "_modal") and self._modal.winfo_exists():
            self._modal.destroy()
        buttons = buttons or (("Aceptar", "primario", None),)
        modal = ctk.CTkFrame(self, fg_color=estilos.FONDO)
        modal.place(relx=0, rely=0, relwidth=1, relheight=1)
        modal.lift()
        self._modal = modal

        card = ctk.CTkFrame(modal, width=420, **estilos.TARJETA)
        card.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(card, text=title, **estilos.ETIQUETA["seccion"]).pack(
            anchor="w", padx=estilos.PAD_TARJETA, pady=(estilos.PAD_TARJETA, 6))
        ctk.CTkLabel(
            card, text=message, wraplength=360, justify="left",
            **estilos.ETIQUETA["cuerpo"],
        ).pack(anchor="w", padx=estilos.PAD_TARJETA, pady=(0, 20))
        actions = ctk.CTkFrame(card, fg_color=estilos.TRANSPARENTE)
        actions.pack(anchor="e", padx=estilos.PAD_TARJETA, pady=(0, estilos.PAD_TARJETA))

        def close():
            if modal.winfo_exists():
                modal.destroy()

        for label, style, callback in buttons:
            action = callback
            command = close if action is None else lambda action=action: (close(), action())
            ctk.CTkButton(
                actions, text=label, command=command,
                **estilos.boton(style, width=110),
            ).pack(side="left", padx=(8, 0))
        modal.bind("<Escape>", lambda _event: close())
        modal.focus_set()

    def _build(self):
        self._init_vars()
        self.view_host = ctk.CTkFrame(self, fg_color=estilos.FONDO)
        self.view_host.pack(fill="both", expand=True)
        self.main_view = self._build_main()
        self.settings_view = self._build_settings()
        self.library = VoiceLibrary(self.view_host, self)
        self.views = {"main": self.main_view, "settings": self.settings_view, "library": self.library}
        self.show("main")

    def _make_meter(self, parent):
        marco = ctk.CTkFrame(parent, **estilos.MEDIDOR_MARCO)
        canvas = tk.Canvas(marco, height=int(estilos.MEDIDOR_ALTO * _escala(self)),
                           bg=estilos.MEDIDOR["fondo"], highlightthickness=0, bd=0)
        canvas.pack(fill="x", padx=18, pady=7)
        canvas.bind("<Configure>", lambda e: self.draw_level(self.last_level))
        self.meters.append(canvas)
        return marco

    # ---- vista principal ----
    def _build_main(self):
        view = ctk.CTkFrame(self.view_host, fg_color=estilos.FONDO)
        acciones = crear_cabecera(view, "", "", marca=True)
        ctk.CTkButton(acciones, text="⚙  Configuración", command=lambda: self.show("settings"),
                      **estilos.boton("secundario", width=156)).pack()
        m, s, p = estilos.MARGEN, estilos.SEPARACION, estilos.PAD_TARJETA

        # Tarjeta central: onda de voz, estado y micrófono para hablar
        self.panel = PanelVoz(view, self)
        self.panel.pack(fill="x", padx=max(m - 14, 0), pady=(0, 0))

        # Fila de control: iniciar/detener + estado
        ctrl = ctk.CTkFrame(view, fg_color=estilos.TRANSPARENTE)
        ctrl.pack(fill="x", padx=m, pady=(0, s))
        self.start_btn = ctk.CTkButton(ctrl, text="Iniciar", command=self.toggle,
                                       **estilos.boton("primario", grande=True, width=168))
        self.start_btn.pack(side="left")
        info = ctk.CTkFrame(ctrl, fg_color=estilos.TRANSPARENTE)
        info.pack(side="left", fill="x", expand=True, padx=(18, 0))
        # Barra de descarga del modelo (solo visible mientras se descarga)
        self.dl_frame = ctk.CTkFrame(info, fg_color=estilos.TRANSPARENTE)
        self.dl_lbl = ctk.CTkLabel(self.dl_frame, text="", **estilos.ETIQUETA["suave"])
        self.dl_lbl.pack(anchor="w", pady=(0, 6))
        self.dl_bar = ctk.CTkProgressBar(self.dl_frame, **estilos.BARRA_PROGRESO)
        self.dl_bar.pack(fill="x")
        self.dl_indeterminate = False
        self.status_lbl = ctk.CTkLabel(info, textvariable=self.status_var, **estilos.ETIQUETA["estado"])
        self.status_lbl.pack(anchor="w")
        self.hint_lbl = ctk.CTkLabel(info, text="", **estilos.ETIQUETA["suave"])
        self.hint_lbl.pack(anchor="w")
        self._update_hotkey_hint()

        # Tarjeta: voz activa
        voz = ctk.CTkFrame(view, **estilos.TARJETA)
        voz.pack(fill="x", padx=m, pady=(0, s))
        self.voice_avatar_box = ctk.CTkFrame(voz, fg_color=estilos.TRANSPARENTE)
        self.voice_avatar_box.pack(side="left", padx=(p - 4, 16), pady=p - 6)
        ctk.CTkButton(voz, text="Elegir voz", command=lambda: self.show("library"),
                      **estilos.boton("secundario", width=124)).pack(side="right", padx=p)
        info_voz = ctk.CTkFrame(voz, fg_color=estilos.TRANSPARENTE)
        info_voz.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info_voz, text="VOZ ACTIVA", **estilos.ETIQUETA["micro"]).pack(anchor="w")
        self.voice_name_lbl = ctk.CTkLabel(info_voz, text="", **estilos.ETIQUETA["nombre_voz"])
        self.voice_name_lbl.pack(anchor="w")
        self.voice_id_lbl = ctk.CTkLabel(info_voz, text="", **estilos.ETIQUETA["micro"])
        self.voice_id_lbl.pack(anchor="w")

        # Tarjeta: probar voz
        prueba = ctk.CTkFrame(view, **estilos.TARJETA)
        prueba.pack(fill="x", padx=m, pady=(0, m), side="bottom")
        ctk.CTkLabel(prueba, text="Probar voz", **estilos.ETIQUETA["cuerpo"]).pack(
            side="left", padx=(p, 12), pady=p - 6)
        self.test_btn = ctk.CTkButton(prueba, text="Probar", command=self.test_voice,
                                      **estilos.boton("primario", width=96))
        self.test_btn.pack(side="right", padx=(10, p - 4))
        self.test_entry = ctk.CTkEntry(prueba, textvariable=self.test_var, **estilos.ENTRADA_TEXTO)
        self.test_entry.pack(side="left", fill="x", expand=True)
        self.test_entry.bind("<Control-Return>", lambda _event: self.test_voice())

        # Tarjeta: actividad
        act = ctk.CTkFrame(view, **estilos.TARJETA)
        act.pack(fill="both", expand=True, padx=m, pady=(0, s))
        ctk.CTkLabel(act, text="ACTIVIDAD", **estilos.ETIQUETA["micro"]).pack(
            anchor="w", padx=p, pady=(p - 8, 6))
        self.log_txt = ctk.CTkTextbox(act, height=100, state="disabled", **estilos.CUADRO_TEXTO)
        self.log_txt.pack(fill="both", expand=True, padx=p - 8, pady=(0, p - 8))

        self.refresh_voice_card()
        return view

    def _update_hotkey_hint(self):
        if hasattr(self, "hint_lbl"):
            self.hint_lbl.configure(
                text=f"También puedes mantener pulsada la tecla {self.key_var.get().upper()} para hablar.")
        if hasattr(self, "panel"):
            self.panel.actualizar_texto()

    # ---- vista de configuración ----
    def _reg(self, widget):
        self.controls.append(widget)
        return widget

    def _seccion(self, parent, titulo, subtitulo):
        card = ctk.CTkFrame(parent, **estilos.TARJETA)
        card.pack(fill="x", padx=6, pady=(0, estilos.SEPARACION))
        card.filas_creadas = 0
        self._n_seccion = getattr(self, "_n_seccion", 0) + 1
        cab = ctk.CTkFrame(card, fg_color=estilos.TRANSPARENTE)
        cab.pack(fill="x", padx=estilos.PAD_TARJETA, pady=(estilos.PAD_TARJETA - 4, 0))
        ctk.CTkLabel(cab, text=f"{self._n_seccion:02d}", width=34, **estilos.NUMERO).pack(
            side="left", padx=(0, 10))
        ctk.CTkLabel(cab, text=titulo, **estilos.ETIQUETA["seccion"]).pack(side="left")
        ctk.CTkLabel(card, text=subtitulo, **estilos.ETIQUETA["suave"]).pack(
            anchor="w", padx=estilos.PAD_TARJETA, pady=(4, 6))
        return card

    def _fila(self, card, etiqueta, ayuda=None):
        """Añade una fila 'etiqueta | control' a una sección y devuelve el marco del control."""
        if card.filas_creadas:
            ctk.CTkFrame(card, height=1, fg_color=estilos.BORDES).pack(
                fill="x", padx=estilos.PAD_TARJETA)
        card.filas_creadas += 1
        fila = ctk.CTkFrame(card, fg_color=estilos.TRANSPARENTE)
        fila.pack(fill="x", padx=estilos.PAD_TARJETA, pady=estilos.PAD_FILA)
        fila.grid_columnconfigure(0, minsize=estilos.ANCHO_ETIQUETA)
        fila.grid_columnconfigure(1, weight=1)
        textos = ctk.CTkFrame(fila, fg_color=estilos.TRANSPARENTE)
        textos.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(textos, text=etiqueta, **estilos.ETIQUETA["cuerpo"]).pack(anchor="w")
        if ayuda:
            ctk.CTkLabel(textos, text=ayuda, wraplength=estilos.ANCHO_ETIQUETA - 12,
                         **estilos.ETIQUETA["suave"]).pack(anchor="w")
        control = ctk.CTkFrame(fila, fg_color=estilos.TRANSPARENTE)
        control.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        return control

    def _combo(self, parent, variable, values):
        cb = ctk.CTkComboBox(parent, variable=variable, values=values, state="readonly",
                             command=lambda _v: self.save(), **estilos.DESPLEGABLE)
        cb.pack(fill="x")
        cb.bind("<Configure>", lambda _event: self._fit_combo_dropdown(cb), add="+")
        self.after_idle(lambda: self._fit_combo_dropdown(cb))
        return self._reg(cb)

    @staticmethod
    def _fit_combo_dropdown(combo):
        """Hace que el menú tenga al menos el ancho visible del combo."""
        width = combo.winfo_width()
        if width <= 1 or not hasattr(combo, "_dropdown_menu"):
            return
        values = combo.cget("values") or []
        char_width = max(tkfont.Font(font=estilos.FUENTE_CUERPO).measure("0"), 1)
        menu_width = max((len(str(value)) for value in values), default=0)
        menu_width = max(menu_width, int((width - 10) / char_width))
        combo._dropdown_menu.configure(min_character_width=menu_width)

    def _build_settings(self):
        view = ctk.CTkFrame(self.view_host, fg_color=estilos.FONDO)
        crear_cabecera(view, "Ajustes", "",
                       "Dispositivos, tecla, claves y ajustes de Fish Audio.",
                       volver=self.show_main)
        scroll = SmoothScrollableFrame(view, **estilos.SCROLL)
        scroll.pack(fill="both", expand=True, padx=estilos.MARGEN - 6, pady=(0, estilos.MARGEN - 6))

        self.lock_banner = ctk.CTkLabel(
            scroll, text="La app está activa: pulsa Detener para cambiar estos ajustes.",
            **estilos.AVISO)

        # 1. Dispositivos de audio
        card = self._seccion(scroll, "Dispositivos de audio",
                             "Micrófono de entrada y salida hacia el cable virtual.")
        self.first_card = card
        self.in_cb = self._combo(self._fila(card, "Micrófono (entrada)"),
                                 self.in_var, [n for n, _ in self.inputs])
        self.out_cb = self._combo(self._fila(card, "Salida (cable virtual)"),
                                  self.out_var, [n for n, _ in self.outputs])
        ctl = self._fila(card, "Dispositivos nuevos", "Vuelve a buscar micrófonos y salidas.")
        self.refresh_btn = self._reg(ctk.CTkButton(
            ctl, text="Actualizar lista", command=self.refresh_devices,
            **estilos.boton("secundario", width=150)))
        self.refresh_btn.pack(anchor="e")

        # 2. Autoescucha
        card = self._seccion(scroll, "Autoescucha",
                             "Oye también por tus altavoces o auriculares lo que se genera.")
        ctl = self._fila(card, "Activar autoescucha")
        self.cb_monitor = self._reg(ctk.CTkSwitch(
            ctl, text="", variable=self.monitor_var, command=self.save,
            **estilos.INTERRUPTOR))
        self.cb_monitor.pack(anchor="e")
        self.mon_cb = self._combo(self._fila(card, "Dispositivo de autoescucha"),
                                  self.mondev_var, [n for n, _ in self.outputs])

        # 3. Entrada de voz
        card = self._seccion(scroll, "Entrada de voz",
                             "Cómo se activa el micrófono y cuándo se considera silencio.")
        ctl = self._fila(card, "Tecla para hablar", "Una letra se escribirá también en otras apps.")
        self.key_btn = self._reg(ctk.CTkButton(
            ctl, text="Cambiar", command=self.change_key, **estilos.boton("primario", width=100)))
        self.key_btn.pack(side="right")
        ctk.CTkLabel(ctl, textvariable=self.key_var, **estilos.TECLA).pack(side="right", padx=(0, 10))
        ctl = self._fila(card, "Sensibilidad (silencio)", "Más a la izquierda detecta voz más baja.")
        self.thr_lbl = ctk.CTkLabel(ctl, text=f"{self.cfg['silence_rms']:.3f}", width=52,
                                    **estilos.ETIQUETA["cuerpo"])
        self.thr_lbl.pack(side="right", padx=(10, 0))
        self.thr_scale = ctk.CTkSlider(ctl, from_=0.001, to=0.05, variable=self.thr_var,
                                       command=self.on_thr, **estilos.DESLIZADOR)
        self.thr_scale.pack(side="left", fill="x", expand=True)
        self.thr_scale.bind("<ButtonRelease-1>", lambda e: self.save())
        ctl = self._fila(card, "Nivel del micrófono", "Con la app iniciada, ajusta el umbral.")
        self._make_meter(ctl).pack(fill="x")

        # 4. Fish Audio
        card = self._seccion(scroll, "Fish Audio", "Acceso y modelo para generar la voz.")
        ctl = self._fila(card, "Clave API")
        self.show_key_btn = ctk.CTkButton(ctl, text="Mostrar", command=self._toggle_key,
                                          **estilos.boton("secundario", width=84))
        self.show_key_btn.pack(side="right", padx=(8, 0))
        self.api_entry = self._reg(ctk.CTkEntry(ctl, textvariable=self.api_var, show="•",
                                                **estilos.ENTRADA_TEXTO))
        self.api_entry.pack(side="left", fill="x", expand=True)
        self.api_entry.bind("<FocusOut>", lambda e: self.save())
        self.fishmodel_entry = self._reg(ctk.CTkEntry(
            self._fila(card, "Modelo Fish"), textvariable=self.fishmodel_var, **estilos.ENTRADA_TEXTO))
        self.fishmodel_entry.pack(fill="x")
        self.fishmodel_entry.bind("<FocusOut>", lambda e: self.save())

        # 5. Controles de audio de Fish Audio
        card = self._seccion(scroll, "Controles de audio (Fish Audio)",
                             "Ajustes opcionales que se envían al generar la voz.")
        nota = ("No documentado en la API: no se envía." if not TAG_COMPAT_PARAM
                else "Se envía a la API.")
        for texto, var, ayuda, attr in (
                ("Normalización de volumen", self.normvol_var, None, "cb_normvol"),
                ("Normalización de texto", self.normtext_var, None, "cb_normtext"),
                ("Compatibilidad de etiquetas", self.tagcompat_var, nota, "cb_tagcompat")):
            sw = self._reg(ctk.CTkSwitch(self._fila(card, texto, ayuda), text="", variable=var,
                                         command=self.save, **estilos.INTERRUPTOR))
            sw.pack(anchor="e")
            setattr(self, attr, sw)
        ctl = self._fila(card, "Valores por defecto", "Desactiva las tres opciones.")
        self.reset_btn = self._reg(ctk.CTkButton(
            ctl, text="Restablecer a normal", command=self.reset_audio,
            **estilos.boton("secundario", width=170)))
        self.reset_btn.pack(anchor="e")

        # 6. Reconocimiento de voz
        card = self._seccion(scroll, "Reconocimiento de voz (Whisper)",
                             "Transcribe lo que dices antes de enviarlo a Fish Audio.")
        self.model_cb = self._combo(
            self._fila(card, "Modelo Whisper", "Más grande = más preciso, pero más lento."),
            self.model_var, WHISPER_MODELS)
        ctl = self._fila(
            card,
            "Token de Hugging Face",
            "Opcional. Aumenta el límite de descarga de los modelos Whisper.",
        )
        self.hf_token_entry = self._reg(ctk.CTkEntry(
            ctl,
            textvariable=self.hf_token_var,
            show="•",
            **estilos.ENTRADA_TEXTO,
        ))
        self.hf_token_entry.pack(fill="x")
        self.hf_token_entry.bind("<FocusOut>", lambda e: self.save())

        footer = ctk.CTkFrame(scroll, fg_color=estilos.TRANSPARENTE, height=28)
        footer.pack(fill="x", padx=estilos.MARGEN, pady=(8, 8))
        footer.pack_propagate(False)
        footer_content = ctk.CTkFrame(footer, fg_color=estilos.TRANSPARENTE)
        footer_content.pack(anchor="center")
        ctk.CTkLabel(
            footer_content, text="Beta · ", **estilos.ETIQUETA["suave_centro"]
        ).pack(side="left")
        enlace = ctk.CTkLabel(
            footer_content, text="JC",
            font=estilos.FUENTE_MICRO_NEGRITA,
            text_color=estilos.ACENTO,
            cursor="hand2",
        )
        enlace.pack(side="left")
        enlace.bind("<Button-1>", lambda _event: webbrowser.open(
            "https://miketrollyt.github.io/JC"
        ))
        return view

    def _toggle_key(self):
        visible = self.api_entry.cget("show") == ""
        self.api_entry.configure(show="•" if visible else "")
        self.show_key_btn.configure(text="Mostrar" if visible else "Ocultar")

    # ---- navegación ----
    def show(self, name):
        for view in self.views.values():
            view.pack_forget()
        if name == "library":
            self.library.show_list()
        self.views[name].pack(fill="both", expand=True)

    def show_main(self):
        self.show("main")

    # ---- voz activa y portadas ----
    def current_voice(self):
        vid = self.cfg["fish_voice_id"]
        for v in self.cfg["voices"]:
            if v["id"] == vid:
                return v["name"], vid
        return DEFAULT_VOICE_LABEL, ""

    def refresh_voice_card(self):
        name, vid = self.current_voice()
        for w in self.voice_avatar_box.winfo_children():
            w.destroy()
        self.make_avatar(self.voice_avatar_box, vid, name, estilos.AVATAR_PRINCIPAL).pack()
        self.voice_name_lbl.configure(text=name)
        self.voice_id_lbl.configure(text=vid or "Sin voz personalizada")

    def select_voice(self, vid):
        self.cfg["fish_voice_id"] = vid
        save_config(self.cfg)
        self.refresh_voice_card()

    def make_avatar(self, parent, vid, name, size):
        """Foto redondeada de la voz; si aún no hay foto, un recuadro con la inicial."""
        if vid:
            self.request_cover(vid)
            img = self.cover_image(vid, size)
            if img:
                return ctk.CTkLabel(parent, image=img, text="", width=size, height=size)
        initial = (name[:1] or "?").upper() if vid else "♪"
        return ctk.CTkLabel(parent, text=initial, width=size, height=size,
                            font=(estilos.FUENTE, size // 2, "bold"),
                            **{**estilos.AVATAR_VACIO, "corner_radius": size // 2})

    def cover_image(self, vid, size):
        pil = self.covers.get(vid)
        if pil is None:
            return None
        key = (vid, size)
        if key not in self._cover_cache:
            self._cover_cache[key] = ctk.CTkImage(light_image=pil, size=(size, size))
        return self._cover_cache[key]

    def refresh_library(self):
        if self.library.winfo_ismapped():
            self.library.render()

    def _set_cover(self, vid, data):
        try:
            px = estilos.AVATAR_PIXELES
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            img = ImageOps.fit(img, (px, px), Image.LANCZOS)
            mask = Image.new("L", (px, px), 0)
            radio = int(px * estilos.RADIO_AVATAR / estilos.AVATAR_PRINCIPAL)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, px - 1, px - 1), radius=radio, fill=255)
            img.putalpha(mask)
            self.covers[vid] = img
        except Exception:  # noqa: BLE001
            self.cover_failed.add(vid)

    def request_cover(self, vid):
        if vid in self.covers or vid in self.cover_pending or vid in self.cover_failed:
            return
        path = os.path.join(COVERS_DIR, vid + ".webp")
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    self._set_cover(vid, f.read())
                return
            except OSError:
                pass
        self.cover_pending.add(vid)

        def fetch():
            try:
                r = requests.get(COVER_URL.format(vid), timeout=15)
                if r.status_code == 200 and r.content:
                    try:
                        os.makedirs(COVERS_DIR, exist_ok=True)
                        with open(path, "wb") as f:
                            f.write(r.content)
                    except OSError:
                        pass
                    self.ui_q.put(("cover", (vid, r.content)))
                    return
            except requests.RequestException:
                pass
            self.ui_q.put(("cover", (vid, None)))

        threading.Thread(target=fetch, daemon=True).start()

    # ---- acciones ----
    def save(self):
        self.collect_cfg()
        save_config(self.cfg)

    def reset_audio(self):
        """Vuelve a los ajustes normales: las tres opciones desactivadas."""
        self.normvol_var.set(False)
        self.normtext_var.set(False)
        self.tagcompat_var.set(False)
        self.save()

    def draw_level(self, val):
        self.last_level = val
        thr = float(self.thr_var.get())
        esc = _escala(self)
        for c in self.meters:
            if not c.winfo_exists():
                continue
            dibujar_medidor(c, val, thr, esc)

    def on_thr(self, _value=None):
        v = float(self.thr_var.get())
        self.thr_lbl.configure(text=f"{v:.3f}")
        self.engine.silence_rms = v
        self.draw_level(self.last_level)

    def append_log(self, text):
        self.log_txt.configure(state="normal")
        self.log_txt.insert("end", text + "\n")
        self.log_txt.see("end")
        self.log_txt.configure(state="disabled")

    def set_controls(self, enabled):
        for w in self.controls:
            if isinstance(w, ctk.CTkComboBox):
                w.configure(state="readonly" if enabled else "disabled")
            else:
                w.configure(state="normal" if enabled else "disabled")
        if enabled:
            self.lock_banner.pack_forget()
        else:
            self.lock_banner.pack(fill="x", padx=6, pady=(0, estilos.SEPARACION), before=self.first_card)

    def refresh_devices(self):
        try:
            sd._terminate()
            sd._initialize()
            self.inputs, self.outputs = list_devices()
        except Exception as e:  # noqa: BLE001
            self.append_log(f"No se pudo actualizar: {e}")
            return
        self.in_cb.configure(values=[n for n, _ in self.inputs])
        self.out_cb.configure(values=[n for n, _ in self.outputs])
        self.mon_cb.configure(values=[n for n, _ in self.outputs])
        for combo in (self.in_cb, self.out_cb, self.mon_cb):
            self._fit_combo_dropdown(combo)
        self.in_var.set(self._select(self.inputs, self.in_var.get(), default_idx=self._default_in()))
        self.out_var.set(self._select(self.outputs, self.out_var.get(), prefer="cable input",
                                      default_idx=self._default_out()))
        self.mondev_var.set(self._select(self.outputs, self.mondev_var.get(),
                                         default_idx=self._default_out()))
        self.save()
        self.append_log("Dispositivos actualizados.")

    def change_key(self):
        import keyboard

        self.key_btn.configure(state="disabled", text="Pulsa una tecla…")

        def capture():
            name = None
            try:
                while True:
                    ev = keyboard.read_event()
                    if ev.event_type == "down":
                        name = ev.name
                        break
            except Exception:  # noqa: BLE001
                pass
            self.ui_q.put(("key", name))

        threading.Thread(target=capture, daemon=True).start()

    def _resolve_devices(self):
        in_idx = dict(self.inputs).get(self.in_var.get())
        out_idx = dict(self.outputs).get(self.out_var.get())
        return in_idx, out_idx

    def _out_devices(self):
        """Lista de salidas: el cable virtual y, si está activada, la autoescucha."""
        _, out_idx = self._resolve_devices()
        if out_idx is None:
            return None
        devs = [out_idx]
        if self.monitor_var.get():
            mon = dict(self.outputs).get(self.mondev_var.get())
            if mon is not None and mon != out_idx:
                devs.append(mon)
        return devs

    def toggle(self):
        if self.running:
            self.engine.stop()
            self.start_btn.configure(state="disabled")
            return
        self.save()
        in_idx, out_idx = self._resolve_devices()
        if in_idx is None or out_idx is None:
            self.show_modal("Dispositivos", "Elige un micrófono y una salida en Configuración.")
            return
        if not self.cfg["fish_api_key"]:
            self.show_modal("Fish Audio", "Falta la clave API de Fish Audio (en Configuración).")
            return
        self.running = True
        self.set_controls(False)
        self.start_btn.configure(text="Detener", **estilos.colores_boton("peligro"))
        self.engine.start(self.cfg, in_idx, self._out_devices())

    def test_voice(self):
        self.save()
        out_idx = self._out_devices()
        text = ensure_final_period(self.test_var.get())
        if not out_idx or not text:
            return
        self.append_log("Probando voz...")
        threading.Thread(
            target=lambda: speak(text, dict(self.cfg), out_idx, lambda m: self.ui_q.put(("log", m))),
            daemon=True,
        ).start()

    def show_download(self, val):
        """val = None (ocultar), (0, 0) (empezando) o (hecho, total) en bytes."""
        if val is None:
            if self.dl_indeterminate:
                self.dl_bar.stop()
                self.dl_indeterminate = False
            self.dl_frame.pack_forget()
            return
        if not self.dl_frame.winfo_ismapped():
            self.dl_frame.pack(fill="x", pady=(0, 8), before=self.status_lbl)
        done, total = val
        if not total:
            if not self.dl_indeterminate:
                self.dl_bar.configure(mode="indeterminate")
                self.dl_bar.start()
                self.dl_indeterminate = True
            self.dl_lbl.configure(text="Preparando la descarga del modelo Whisper…")
            return
        if self.dl_indeterminate:
            self.dl_bar.stop()
            self.dl_bar.configure(mode="determinate")
            self.dl_indeterminate = False
        frac = min(done / total, 1.0)
        self.dl_bar.set(frac)
        self.dl_lbl.configure(
            text=f"Descargando modelo Whisper… {frac * 100:.0f} %  ({done / 1e6:.0f} MB de {total / 1e6:.0f} MB)")

    def _style_status(self, text):
        if text.startswith("Grabando"):
            color = estilos.PELIGRO
        elif text.startswith("Detenido"):
            color = estilos.TEXTO_SECUNDARIO
        else:
            color = estilos.TEXTO
        self.status_lbl.configure(text_color=color)
        self.panel.set_estado(text)

    def poll(self):
        try:
            while True:
                kind, val = self.ui_q.get_nowait()
                try:
                    self._handle(kind, val)
                except Exception as e:  # noqa: BLE001
                    # un fallo en un mensaje no debe parar la interfaz
                    self.append_log(f"Error en la interfaz ({kind}): {e}")
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def _handle(self, kind, val):
        if kind == "log":
            self.append_log(val)
        elif kind == "status":
            self.status_var.set(val)
            self._style_status(val)
        elif kind == "download":
            self.show_download(val)
        elif kind == "level":
            self.draw_level(val)
        elif kind == "running":
            self.running = bool(val)
            if not self.running:
                self.set_controls(True)
                self.start_btn.configure(text="Iniciar", state="normal",
                                         **estilos.colores_boton("primario"))
                self.draw_level(0.0)
        elif kind == "cover":
            vid, data = val
            self.cover_pending.discard(vid)
            if data is None:
                self.cover_failed.add(vid)
            else:
                self._set_cover(vid, data)
            self.refresh_library()
            self.refresh_voice_card()
        elif kind == "key":
            self.key_btn.configure(state="normal", text="Cambiar")
            if val:
                self.key_var.set(val)
                self.save()

    def on_close(self):
        try:
            self.save()
        finally:
            self.engine.stop()
            self.destroy()


if __name__ == "__main__":
    cargar_fuentes()
    App().mainloop()