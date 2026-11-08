import customtkinter as ctk

# ------------------------------- COLORES -------------------------------

FONDO = "#F6F4EE"                 # paper
PANEL = "#FFFDF8"
PANEL_ALTERNATIVO = "#EFEADD"
ENTRADA = "#F8F6EF"
TEXTO = "#1C1E26"                 # ink
TEXTO_SECUNDARIO = "#76705F"      # gris cálido para párrafos y ayudas
TEXTO_MICRO = "#8C8573"           # etiquetas pequeñas en mono
TEXTO_DESACTIVADO = "#A69C89"
TEXTO_SOBRE_COLOR = "#1C1E26"
TINTA_ACTIVA = "#343846"          # hover de los botones oscuros
PRIMARIO = "#F2B705"              # myna
PRIMARIO_ACTIVO = "#D99F00"
ACENTO = "#6B4A3B"                # bark
ACENTO_ACTIVO = "#56392E"
PELIGRO = "#B94E48"
PELIGRO_ACTIVO = "#9E3E39"
PELIGRO_SUAVE = "#F7E5DF"
BORDES = "#E2DCCD"
SOMBRA = "#E8E2D5"
INTERRUPTOR_APAGADO = "#CFC8B8"
TRANSPARENTE = "transparent"

# ------------------------------ TIPOGRAFÍAS ------------------------------

FUENTE = "Geist"
FUENTE_MONO = "Geist Mono"
FUENTE_SERIF = "Instrument Serif"
FUENTE_TITULO = (FUENTE, 30, "bold")
FUENTE_TITULO_SERIF = (FUENTE_SERIF, 36, "italic")
FUENTE_SECCION = (FUENTE, 14, "bold")
FUENTE_NOMBRE_VOZ = (FUENTE, 18, "bold")
FUENTE_CUERPO = (FUENTE, 12)
FUENTE_NEGRITA = (FUENTE, 12, "bold")
FUENTE_PEQUENA = (FUENTE, 11)
FUENTE_PEQUENA_NEGRITA = (FUENTE, 11, "bold")
FUENTE_MICRO = (FUENTE_MONO, 10)
FUENTE_MICRO_NEGRITA = (FUENTE_MONO, 10, "bold")
FUENTE_BOTON = (FUENTE, 12, "bold")
FUENTE_BOTON_GRANDE = (FUENTE, 14, "bold")
FUENTE_LOG = (FUENTE_MONO, 11)
FUENTE_MEDIDOR = (FUENTE_MONO, 9)

# -------------------------------- MEDIDAS --------------------------------

MARGEN = 22              # margen exterior de cada vista
SEPARACION = 14          # espacio vertical entre tarjetas
PAD_TARJETA = 22         # margen interior de las tarjetas
PAD_FILA = (11, 11)      # espacio vertical de cada fila de ajustes
ANCHO_ETIQUETA = 230     # ancho de la columna de etiquetas en Configuración
RADIO_TARJETA = 26
RADIO_BOTON = 20         # = alto/2: píldora completa
RADIO_BOTON_GRANDE = 26
RADIO_ENTRADA = 18
RADIO_AVATAR = 34        # = AVATAR_PRINCIPAL/2: las fotos son círculos
ALTO_BOTON = 40
ALTO_BOTON_GRANDE = 52
ALTO_ENTRADA = 38
AVATAR_PRINCIPAL = 68    # foto de la voz activa en la vista principal
AVATAR_BIBLIOTECA = 108  # foto en la biblioteca de voces
TARJETA_VOZ_ANCHO = 200  # ancho de cada cuadrito de la biblioteca
TARJETA_VOZ_ALTO = 236   # alto de cada cuadrito de la biblioteca
TARJETA_VOZ_GAP = 8      # separación (por cada lado) entre cuadritos
AVATAR_PIXELES = 192     # resolución interna con la que se guardan las fotos

# ------------------------------- CONTENEDORES -------------------------------

TARJETA = dict(
    fg_color=PANEL,
    corner_radius=RADIO_TARJETA,
    border_width=1,
    border_color=BORDES,
)

TARJETA_ACTIVA = dict(
    fg_color=PANEL,
    corner_radius=RADIO_TARJETA,
    border_width=2,
    border_color=PRIMARIO,
)

PASTILLA = dict(  # contenedor de la insignia de la cabecera (como en la web)
    fg_color=PANEL,
    corner_radius=15,
    border_width=1,
    border_color=BORDES,
)

SCROLL = dict(
    fg_color=TRANSPARENTE,
    scrollbar_button_color=BORDES,
    scrollbar_button_hover_color=TEXTO_DESACTIVADO,
)

AVISO = dict(  # banner informativo (p. ej. "detén la app para cambiar esto")
    fg_color=PELIGRO_SUAVE,
    text_color=PELIGRO,
    corner_radius=17,
    font=FUENTE_PEQUENA_NEGRITA,
    height=34,
)

# --------------------------------- TEXTOS ---------------------------------

ETIQUETA = {
    "titulo": dict(font=FUENTE_TITULO, text_color=TEXTO, anchor="w"),
    "titulo_serif": dict(font=FUENTE_TITULO_SERIF, text_color=ACENTO, anchor="w"),
    "subtitulo": dict(font=FUENTE_CUERPO, text_color=TEXTO_SECUNDARIO, anchor="w"),
    "seccion": dict(font=FUENTE_SECCION, text_color=TEXTO, anchor="w"),
    "cuerpo": dict(font=FUENTE_CUERPO, text_color=TEXTO, anchor="w"),
    "suave": dict(font=FUENTE_PEQUENA, text_color=TEXTO_SECUNDARIO, anchor="w", justify="left"),
    "micro": dict(font=FUENTE_MICRO, text_color=TEXTO_MICRO, anchor="w"),
    "nombre_voz": dict(font=FUENTE_NOMBRE_VOZ, text_color=TEXTO, anchor="w"),
    "estado": dict(font=FUENTE_MICRO_NEGRITA, text_color=TEXTO_SECUNDARIO, anchor="w", justify="left"),
    "vacio": dict(font=FUENTE_SECCION, text_color=TEXTO, anchor="center"),
    "nombre_cuadro": dict(font=(FUENTE, 14, "bold"), text_color=TEXTO, anchor="center"),
    "suave_centro": dict(font=FUENTE_MICRO, text_color=TEXTO_MICRO, anchor="center"),
}

INSIGNIA = dict(  # pastilla amarilla en mono, como "OPEN SOURCE" en la web
    fg_color=PRIMARIO,
    text_color=TEXTO,
    corner_radius=12,
    font=FUENTE_MICRO_NEGRITA,
    height=24,
)

NUMERO = dict(  # numerito de cada sección de Configuración
    fg_color=PRIMARIO,
    text_color=TEXTO,
    corner_radius=11,
    font=FUENTE_MICRO_NEGRITA,
    height=22,
)

TECLA = dict(  # recuadro que muestra la tecla de hablar
    fg_color=PANEL_ALTERNATIVO,
    text_color=TEXTO,
    corner_radius=RADIO_BOTON,
    font=(FUENTE_MONO, 12, "bold"),
    height=ALTO_BOTON,
    width=110,
)

AVATAR_VACIO = dict(  # círculo con la inicial cuando no hay foto
    fg_color=PANEL_ALTERNATIVO,
    text_color=ACENTO,
    corner_radius=RADIO_AVATAR,
)

# --------------------------------- BOTONES ---------------------------------

COLORES_BOTON = {
    # El botón principal es oscuro, como el "Ver en GitHub" de la web
    "primario": dict(fg_color=TEXTO, hover_color=TINTA_ACTIVA,
                     text_color="#F6F4EE", text_color_disabled="#8D8F99"),
    "amarillo": dict(fg_color=PRIMARIO, hover_color=PRIMARIO_ACTIVO,
                     text_color=TEXTO_SOBRE_COLOR, text_color_disabled="#8A6A00"),
    "acento": dict(fg_color=ACENTO, hover_color=ACENTO_ACTIVO,
                   text_color="#F6F4EE", text_color_disabled="#D8CDC7"),
    "peligro": dict(fg_color=PELIGRO, hover_color=PELIGRO_ACTIVO,
                    text_color="#F6F4EE", text_color_disabled="#E4C2BD"),
    "secundario": dict(fg_color=PANEL, hover_color=PANEL_ALTERNATIVO,
                       text_color=TEXTO, text_color_disabled=TEXTO_DESACTIVADO,
                       border_width=1, border_color=BORDES),
    "peligro_suave": dict(fg_color=PANEL_ALTERNATIVO, hover_color=PELIGRO_SUAVE,
                          text_color=PELIGRO, text_color_disabled=TEXTO_DESACTIVADO),
}


def colores_boton(tipo):
    """Solo los colores de un botón (para cambiar su aspecto sin tocar el tamaño)."""
    return dict(COLORES_BOTON[tipo])


def boton(tipo="primario", grande=False, **extra):
    """Estilo completo de un botón: tipo = primario | amarillo | acento | peligro | secundario | peligro_suave."""
    kw = dict(corner_radius=RADIO_BOTON, height=ALTO_BOTON, font=FUENTE_BOTON, border_width=0)
    if grande:
        kw.update(corner_radius=RADIO_BOTON_GRANDE, height=ALTO_BOTON_GRANDE,
                  font=FUENTE_BOTON_GRANDE)
    kw.update(COLORES_BOTON[tipo])
    kw.update(extra)
    return kw


# ------------------------------ CAMPOS DE ENTRADA ------------------------------

ENTRADA_TEXTO = dict(
    fg_color=ENTRADA,
    border_color=BORDES,
    border_width=1,
    text_color=TEXTO,
    placeholder_text_color=TEXTO_DESACTIVADO,
    height=ALTO_ENTRADA,
    corner_radius=RADIO_ENTRADA,
    font=FUENTE_CUERPO,
)

DESPLEGABLE = dict(
    fg_color=ENTRADA,
    border_color=BORDES,
    border_width=1,
    button_color=PANEL_ALTERNATIVO,
    button_hover_color=BORDES,
    text_color=TEXTO,
    dropdown_fg_color=PANEL,
    dropdown_hover_color=PANEL_ALTERNATIVO,
    dropdown_text_color=TEXTO,
    height=ALTO_ENTRADA,
    corner_radius=RADIO_ENTRADA,
    font=FUENTE_CUERPO,
    dropdown_font=FUENTE_CUERPO,
)

INTERRUPTOR = dict(
    fg_color=INTERRUPTOR_APAGADO,
    progress_color=PRIMARIO,
    button_color=TEXTO,
    button_hover_color=TINTA_ACTIVA,
    text_color=TEXTO,
    font=FUENTE_CUERPO,
    switch_width=46,
    switch_height=24,
    width=46,
    height=26,
)

DESLIZADOR = dict(
    fg_color=BORDES,
    progress_color=PRIMARIO,
    button_color=TEXTO,
    button_hover_color=TINTA_ACTIVA,
)

BARRA_PROGRESO = dict(  # descarga del modelo Whisper
    fg_color=BORDES,
    progress_color=PRIMARIO,
    height=8,
    corner_radius=4,
)

CUADRO_TEXTO = dict(  # registro de actividad
    fg_color=ENTRADA,
    border_width=1,
    border_color=BORDES,
    text_color=TEXTO,
    corner_radius=16,
    font=FUENTE_LOG,
    wrap="word",
)

# ------------------------------ MEDIDOR DE NIVEL ------------------------------

MEDIDOR = {
    "fondo": ENTRADA,
    "borde": BORDES,
    "barra_activa": PRIMARIO,      # segmentos encendidos con voz
    "barra_baja": "#B7AC96",       # segmentos encendidos por debajo del umbral
    "barra_inactiva": "#DDD7C8",   # segmentos apagados
    "umbral": TEXTO,               # segmento que marca el umbral
    "texto": TEXTO_MICRO,
}

MEDIDOR_MARCO = dict(  # contenedor en píldora del medidor
    fg_color=MEDIDOR["fondo"],
    border_color=MEDIDOR["borde"],
    border_width=1,
    corner_radius=18,
)
MEDIDOR_ALTO = 18


def aplicar(root):
    """Aplica el tema base antes de construir los widgets."""
    ctk.set_appearance_mode("light")
    root.configure(fg_color=FONDO)