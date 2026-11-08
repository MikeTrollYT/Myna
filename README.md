<div align="center">

<img src="img/logo.svg" alt="Myna STT" width="140">

# Myna STT

**Habla con tu micrófono y que otra voz lo diga por ti.**

Reconocimiento de voz local con Whisper + síntesis de voz con IA mediante Fish Audio.

![Python](https://img.shields.io/badge/Python-3.10%2B-2D7A68?style=flat-square&logo=python&logoColor=white)
![Plataforma](https://img.shields.io/badge/Windows-0078D4?style=flat-square&logo=windows&logoColor=white)
![Whisper](https://img.shields.io/badge/Whisper-local-D9826B?style=flat-square)
![Fish Audio](https://img.shields.io/badge/Fish%20Audio-TTS-236251?style=flat-square)

</div>

---

## ¿Qué es?

Myna STT es una aplicación de escritorio con interfaz gráfica que funciona como un *push-to-talk* con voz de IA:

1. Mantienes pulsada una tecla (o el botón de la ventana) y hablas.
2. Mientras hablas, **Whisper** transcribe tu voz en local, por trozos.
3. Al soltar, el texto se envía a **Fish Audio**, que lo convierte en la voz que hayas elegido.
4. El audio se reproduce en el dispositivo de salida que configures, normalmente un cable virtual como **VB-Cable**, para usarlo como micrófono en Discord, OBS, juegos, etc.

## Características

- Transcripción **local** con Whisper (`base`, `small`, `medium` o `large-v3-turbo`), sin enviar tu audio a ningún servidor.
- **Biblioteca de voces** con fotos: guarda tantas voces de Fish Audio como quieras y cambia entre ellas con un clic.
- Tecla para hablar configurable (por defecto `F9`).
- **Autoescucha**: oye también en tus auriculares lo que se genera.
- Medidor de nivel del micrófono y sensibilidad ajustable para detectar el silencio.
- Descarga automática de los modelos Whisper, con barra de progreso y reanudación si se corta.
- Botón **Probar voz** para comprobar la salida sin hablar.
- Registro de actividad en la propia ventana.

## Requisitos

- **Windows** (la interfaz y la captura de teclas global están pensadas para este sistema).
- **Python 3.10 o superior**.
- Una cuenta en [Fish Audio](https://fish.audio) con su clave API.
- Un cable de audio virtual, como [VB-Cable](https://vb-audio.com/Cable/), si quieres usar la voz generada como micrófono en otras aplicaciones.

## Instalación

1. Descarga o clona el proyecto:

   ```bash
   git clone <url-del-repositorio>
   cd <carpeta-del-proyecto>
   ```

2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación:

   ```bash
   python myna.py
   ```

Los archivos `myna.py` y `estilos.py` deben estar en la misma carpeta. Al abrir la app se crean junto a ellos `config.json` (tus ajustes), `models/` (modelos Whisper) y `covers/` (fotos de las voces).

## Claves y tokens

Myna STT necesita dos claves. Pégalas en **Configuración** o, si prefieres, defínelas como variables de entorno.

```markdown
# API HF (Descarga rapida)
https://huggingface.co/settings/tokens

# API Fish Audio
https://fish.audio/es/app/api-keys/
```

| Clave | Dónde conseguirla | ¿Obligatoria? | Variable de entorno |
| --- | --- | --- | --- |
| **API de Fish Audio** | [fish.audio/es/app/api-keys](https://fish.audio/es/app/api-keys/) | Sí | `FISH_API_KEY` |
| **Token de Hugging Face** | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) | No, pero acelera la descarga de modelos | `HF_TOKEN` |

## Cómo se usa

### 1. Configuración inicial

Abre **⚙ Configuración** y rellena, de arriba abajo:

| Sección | Qué hacer |
| --- | --- |
| **Dispositivos de audio** | Elige tu **micrófono** de entrada y como **salida** el cable virtual (por ejemplo, *CABLE Input*). Si conectas algo nuevo, pulsa *Actualizar lista*. |
| **Autoescucha** | Actívala si quieres oír también lo que se genera, y elige tus auriculares o altavoces. |
| **Entrada de voz** | Cambia la tecla para hablar con *Cambiar* y ajusta la **sensibilidad**. Con la app iniciada, el medidor te ayuda a colocar el umbral por encima del ruido de fondo. |
| **Fish Audio** | Pega tu **clave API** y, si lo necesitas, el modelo de Fish (por defecto `s2.1-pro-free`). |
| **Controles de audio** | Opcionales: normalización de volumen y de texto. *Restablecer a normal* las desactiva. |
| **Reconocimiento de voz (Whisper)** | Elige el modelo y, si quieres, pega tu token de Hugging Face. |

Los ajustes se guardan solos.

### 2. Elegir una voz

Pulsa **Elegir voz** en la ventana principal para abrir la **Biblioteca de voces**.

- **+ Añadir voz**: escribe un nombre y pega el **ID o el enlace** de la voz de Fish Audio. Se guarda en la biblioteca con su foto.
- **Usar**: activa esa voz. La voz en uso se marca con **✓ En uso**.
- **✕**: elimina la voz de la biblioteca.
- La **Voz por defecto** usa la voz estándar del modelo, sin voz personalizada.

Las voces se muestran en cuadritos que se reorganizan solos según el ancho de la ventana.

### 3. Hablar

1. En la ventana principal pulsa **Iniciar**. La primera vez se descargará el modelo Whisper elegido y verás una barra de progreso.
2. Mantén pulsada la **tecla para hablar** (o el botón **Mantener para hablar**) y di lo que quieras.
3. Suelta la tecla. La voz de IA dirá el texto por la salida configurada.
4. Pulsa **Detener** cuando termines.

### 4. Usarlo en otras aplicaciones

Para que Discord, OBS, juegos o videollamadas oigan la voz de IA:

1. En Myna STT, elige como **salida** el cable virtual (*CABLE Input*).
2. En la otra aplicación, elige como **micrófono** el otro extremo del cable (*CABLE Output*).
3. Activa la **autoescucha** para oír tú mismo lo que se envía.

### 5. Probar sin hablar

En la ventana principal, escribe un texto en **Probar voz** y pulsa **Probar** (o `Ctrl + Enter` desde el campo de texto) para comprobar la voz y la salida de audio. Si el texto no termina en `.`, `?` o `!`, se añade automáticamente un punto antes de enviarlo a Fish Audio. Las solicitudes usan un modo equilibrado de latencia y reproducción PCM por streaming, para empezar a escuchar mientras Fish Audio todavía genera el resto.

## Modelos Whisper

| Modelo | Velocidad | Precisión |
| --- | --- | --- |
| `base` | Muy rápida | Básica |
| `small` | Rápida | Buena (por defecto) |
| `medium` | Media | Muy buena |
| `large-v3-turbo` | Más lenta | La mejor |

Se descargan desde Hugging Face a la carpeta `models/` la primera vez que se usan. Si la descarga se corta o la cancelas, continúa por donde iba.

## Estructura del proyecto

```
.
├── myna.py        # Aplicación: interfaz, Whisper y Fish Audio
├── estilos.py      # Tema visual: colores, fuentes y medidas
├── logo.svg        # Logo
├── config.json     # Tus ajustes (se crea solo, no lo subas)
├── models/         # Modelos Whisper descargados (se crea solo)
└── covers/         # Fotos de las voces (se crea solo)
```

Para cambiar el aspecto de la aplicación solo tienes que editar `estilos.py`.

## Tecnologías

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): reconocimiento de voz local
- [Fish Audio](https://fish.audio): síntesis de voz con IA
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter): interfaz gráfica
- [sounddevice](https://python-sounddevice.readthedocs.io/) y [soundfile](https://python-soundfile.readthedocs.io/): audio
- [keyboard](https://github.com/boppreh/keyboard): tecla global para hablar