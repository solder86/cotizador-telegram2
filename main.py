from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os, tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# =========================
# CONFIGURACIÓN
# =========================
TOKEN = os.environ["BOT_TOKEN"]

BASE_COST = 7000
PROJECT_COST_M2 = 140
ANTICIPO = 0.30

VENDEDOR_TELEGRAM = (
    "https://t.me/ventas_dosp?"
    "text=Hola%20vengo%20del%20cotizador%20de%20naves%20industriales%20"
    "y%20quiero%20continuar%20con%20mi%20proyecto."
)

EQUIPAMIENTO = {
    "básica": {
        "costo": 0,
        "desc": [
            "Estructura metálica principal",
            "Cubierta y fachadas de lámina",
            "Piso industrial de concreto estándar",
            "Instalación eléctrica básica",
            "Preparación para futuras ampliaciones"
        ]
    },
    "intermedio": {
        "costo": 1200,
        "desc": [
            "Estructura metálica reforzada",
            "Cubierta y fachadas industriales",
            "Piso industrial de alta resistencia",
            "Instalación eléctrica industrial",
            "Iluminación LED industrial",
            "Andenes de carga",
            "Área de oficinas administrativas"
        ]
    },
    "premium": {
        "costo": 2500,
        "desc": [
            "Estructura metálica de alto desempeño",
            "Cubierta y fachadas especializadas",
            "Piso industrial de máxima capacidad",
            "Instalación eléctrica avanzada",
            "Iluminación especializada",
            "Sistema HVAC",
            "Sistema contra incendios (sprinklers)",
            "Oficinas equipadas",
            "Cumplimiento de normativa industrial avanzada"
        ]
    }
}

# =========================
# PDF CONSOLIDADO
# =========================
def generar_pdf(datos):
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(f.name, pagesize=letter)
    width, height = letter
    y = height - 40

    # -------- HEADER --------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "DOS-P | Innovación Inmobiliaria")
    y -= 30

    # ===== SECCIÓN 1: NAVE =====
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "1. Cotización Nave Industrial")
    y -= 25

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Superficie: {datos['m2']:,.0f} m²"); y -= 16
    c.drawString(50, y, f"Altura libre: {datos['altura']} m"); y -= 16
    c.drawString(50, y, f"Estado: {datos['estado'].title()}"); y -= 16
    c.drawString(50, y, f"Equipamiento: {datos['equipamiento'].title()}"); y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Incluye:")
    y -= 16

    c.setFont("Helvetica", 11)
    for i in datos["desc"]:
        c.drawString(60, y, f"- {i}")
        y -= 14

    y -= 15
    c.setFont("Helvetica-Bold", 12)
    c.drawString(
        50, y,
        f"Inversión nave: ${datos['nave_min']:,.0f} – ${datos['nave_max']:,.0f} MXN"
    )

    # -------- NUEVA PÁGINA --------
    c.showPage()
    y = height - 40

    # ===== SECCIÓN 2: PROYECTO =====
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "2. Proyecto Ejecutivo")
    y -= 25

    c.setFont("Helvetica", 11)
    c.drawString(50, y, "Incluye:")
    y -= 16
    c.drawString(60, y, "- Mecánica de suelos"); y -= 14
    c.drawString(60, y, "- Cálculo estructural"); y -= 14
    c.drawString(60, y, "- Planos arquitectónicos"); y -= 20

    c.drawString(50, y, f"Área del terreno: {datos['m2_terreno']:,.0f} m²"); y -= 16
    c.drawString(50, y, f"Costo proyecto: ${datos['proy_costo']:,.0f} MXN"); y -= 16
    c.drawString(
        50, y,
        f"Anticipo 30%: ${datos['proy_costo'] * ANTICIPO:,.0f} MXN"
    )

    # -------- NUEVA PÁGINA --------
    c.showPage()
    y = height - 40

    # ===== SECCIÓN 3: RESUMEN =====
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "3. Resumen General del Proyecto")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(
        50, y,
        f"Nave industrial: ${datos['nave_min']:,.0f} – ${datos['nave_max']:,.0f} MXN"
    )
    y -= 18
    c.drawString(50, y, f"Proyecto ejecutivo: ${datos['proy_costo']:,.0f} MXN")
    y -= 25

    total_min = datos['nave_min'] + datos['proy_costo']
    total_max = datos['nave_max'] + datos['proy_costo']

    c.setFont("Helvetica-Bold", 12)
    c.drawString(
        50, y,
        f"Total estimado del proyecto: ${total_min:,.0f} – ${total_max:,.0f} MXN"
    )

    y -= 30
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        50, y,
        "Cotización preliminar, no contractual. Sujeta a proyecto ejecutivo."
    )

    c.showPage()
    c.save()
    return f.name

# =========================
# BOT (MISMA LÓGICA FINAL)
# =========================
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower().strip()

    if texto in ["/start", "cotizar"]:
        context.user_data.clear()
        context.user_data["step"] = "M2"
        await update.message.reply_text("📐 ¿Cuántos m² tendrá la nave?")
        return

    step = context.user_data.get("step")

    if step == "M2":
        context.user_data["m2"] = float(texto)
        context.user_data["step"] = "ALTURA"
        await update.message.reply_text("🏗️ ¿Altura libre en metros?")
        return

    if step == "ALTURA":
        context.user_data["altura"] = float(texto)
        context.user_data["step"] = "ESTADO"
        await update.message.reply_text("📍 ¿En qué estado se construirá?")
        return

    if step == "ESTADO":
        context.user_data["estado"] = texto
        context.user_data["step"] = "EQUIP"
        await update.message.reply_text("Basico / Intermedio / Premium")
        return

    if step == "EQUIP":
        eq = EQUIPAMIENTO[texto]
        m2 = context.user_data["m2"]
        costo_m2 = BASE_COST + eq["costo"]

        nave_min = m2 * costo_m2
        nave_max = nave_min * 1.12

        context.user_data.update({
            "equipamiento": texto,
            "desc": eq["desc"],
            "nave_min": nave_min,
            "nave_max": nave_max,
            "step": "TERRENO"
        })

        await update.message.reply_text(
            f"💰 Nave: ${nave_min:,.0f} – ${nave_max:,.0f} MXN\n"
            "👉 ¿Ya cuentas con el terreno? (Sí / No)"
        )
        return

    if step == "TERRENO":
        if texto in ["si", "sí"]:
            context.user_data["step"] = "DIM"
            await update.message.reply_text("📐 Dimensiones del terreno (ej. 30x50)")
        else:
            context.user_data["proy_costo"] = 0
            context.user_data["m2_terreno"] = 0
            context.user_data["step"] = "PDF"
        return

    if step == "DIM":
        context.user_data["dim"] = texto
        context.user_data["step"] = "PDF"
        await update.message.reply_text("📍 Estado o ciudad del terreno")
        return

    if step == "PDF":
        if "dim" in context.user_data:
            a, l = context.user_data["dim"].replace("m", "").split("x")
            m2_t = float(a) * float(l)
            context.user_data["m2_terreno"] = m2_t
            context.user_data["proy_costo"] = m2_t * PROJECT_COST_M2

        ruta = generar_pdf(context.user_data)

        await update.message.reply_document(
            open(ruta, "rb"),
            caption="📄 Cotización completa de tu proyecto"
        )

        await update.message.reply_text(
            "👉 Lo ideal es continuar este proceso con un asesor especializado\n"
            f"{VENDEDOR_TELEGRAM}\n\n"
            "🔁 Para cotizar nueva obra escribe: cotizar"
        )


    # Mensaje FINAL del bot
await update.message.reply_text(
    "🔁 Para cotizar un nuevo proyecto escribe: cotizar",
    parse_mode="Markdown"
)

        context.user_data.clear()
        return

# =========================
# RUN
# =========================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))
app.run_polling()
