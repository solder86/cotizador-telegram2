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
    "basico": {
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
# PDF
# =========================
def generar_pdf(datos):
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(f.name, pagesize=letter)
    y = 750

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "DOS-P | Innovación Inmobiliaria")
    y -= 30

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Cotización Preliminar – Nave Industrial")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Superficie nave: {datos['m2']:,.0f} m²"); y -= 16
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

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Inversión estimada nave:")
    y -= 16

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"${datos['nave_min']:,.0f} – ${datos['nave_max']:,.0f} MXN")

    c.showPage()
    c.save()
    return f.name

# =========================
# BOT
# =========================
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower().strip()

    # INICIO
    if texto in ["/start", "cotizar"]:
        context.user_data.clear()
        context.user_data["step"] = "NAVE_M2"
        await update.message.reply_text(
            "👷‍♂️ *Cotizador de Naves Industriales*\n\n"
            "📐 ¿Cuántos m² tendrá la nave?",
            parse_mode="Markdown"
        )
        return

    step = context.user_data.get("step")

    # ===== COTIZACIÓN NAVE =====
    if step == "NAVE_M2":
        context.user_data["m2"] = float(texto)
        context.user_data["step"] = "NAVE_ALTURA"
        await update.message.reply_text("🏗️ ¿Altura libre en metros?")
        return

    if step == "NAVE_ALTURA":
        context.user_data["altura"] = float(texto)
        context.user_data["step"] = "NAVE_ESTADO"
        await update.message.reply_text("📍 ¿En qué estado se construirá?")
        return

    if step == "NAVE_ESTADO":
        context.user_data["estado"] = texto
        context.user_data["step"] = "NAVE_EQUIP"
        await update.message.reply_text(
            "⚙️ Nivel de equipamiento:\n\n"
            "🟢 Basico\n🟡 Intermedio\n🔴 Premium\n\n"
            "Escribe: Basico / Intermedio / Premium"
        )
        return

    if step == "NAVE_EQUIP":
        if texto not in EQUIPAMIENTO:
            await update.message.reply_text("Elige: Basico / Intermedio / Premium")
            return

        eq = EQUIPAMIENTO[texto]
        m2 = context.user_data["m2"]
        altura = context.user_data["altura"]
        estado = context.user_data["estado"]

        costo_m2 = BASE_COST + eq["costo"]
        if altura >= 10:
            costo_m2 += 800
        if estado in ["jalisco", "cdmx", "nuevo león"]:
            costo_m2 += 600

        nave_min = m2 * costo_m2
        nave_max = nave_min * 1.12

        context.user_data["nave_min"] = nave_min
        context.user_data["nave_max"] = nave_max

        desglose = "\n".join(f"• {i}" for i in eq["desc"])

        await update.message.reply_text(
            "📐 *Cotización de Nave Industrial*\n\n"
            f"*Incluye:*\n{desglose}\n\n"
            f"💰 *Costo nave:*\n"
            f"${nave_min:,.0f} – ${nave_max:,.0f} MXN",
            parse_mode="Markdown"
        )

        datos_pdf = {
            "m2": m2,
            "altura": altura,
            "estado": estado,
            "equipamiento": texto,
            "desc": eq["desc"],
            "nave_min": nave_min,
            "nave_max": nave_max
        }

        ruta = generar_pdf(datos_pdf)
        context.user_data["ruta_pdf"] = ruta

        await update.message.reply_document(open(ruta, "rb"))

        context.user_data["step"] = "PROY_TERRENO"
        await update.message.reply_text(
            "👉 *Cotiza tu proyecto ejecutivo*\n\n"
            "¿Ya cuentas con el terreno?\n"
            "Responde: *Sí* / *No*",
            parse_mode="Markdown"
        )
        return

    # ===== PROYECTO EJECUTIVO =====
    if step == "PROY_TERRENO":
        if texto in ["si", "sí"]:
            context.user_data["step"] = "PROY_DIM"
            await update.message.reply_text("📐 Dimensiones del terreno (ej. 30x50)")
        else:
            context.user_data["step"] = "CIERRE"
        return

    if step == "PROY_DIM":
        context.user_data["dim"] = texto
        context.user_data["step"] = "PROY_CIUDAD"
        await update.message.reply_text("📍 Estado o ciudad del terreno")
        return

    if step == "PROY_CIUDAD":
        try:
            a, l = context.user_data["dim"].replace("m", "").split("x")
            m2_t = float(a) * float(l)
        except:
            await update.message.reply_text("⚠️ Usa formato: 20x30")
            return

        costo_proy = m2_t * PROJECT_COST_M2
        anticipo = costo_proy * ANTICIPO

        context.user_data["proy_costo"] = costo_proy

        await update.message.reply_text(
            "📐 *Proyecto Ejecutivo*\n"
            "• Mecánica de suelos\n"
            "• Cálculo estructural\n"
            "• Planos arquitectónicos\n\n"
            f"📏 *Área del terreno:* {m2_t:,.0f} m²\n"
            f"💰 *Costo proyecto:* ${costo_proy:,.0f} MXN\n"
            f"🔻 *Anticipo 30%:* ${anticipo:,.0f} MXN",
            parse_mode="Markdown"
        )

        context.user_data["step"] = "CIERRE"
        return

    # ===== CIERRE =====
    if step == "CIERRE":
        nave_min = context.user_data.get("nave_min", 0)
        nave_max = context.user_data.get("nave_max", 0)
        proy = context.user_data.get("proy_costo", 0)

        total_min = nave_min + proy
        total_max = nave_max + proy

        await update.message.reply_text(
            "🧾 *Resumen General del Proyecto*\n\n"
            f"🏗️ Nave industrial: ${nave_min:,.0f} – ${nave_max:,.0f} MXN\n"
            f"📐 Proyecto ejecutivo: ${proy:,.0f} MXN\n\n"
            f"💰 *Total estimado:*\n"
            f"${total_min:,.0f} – ${total_max:,.0f} MXN\n\n"
            "👉 *Lo ideal es continuar este proceso con un asesor especializado.*",
            parse_mode="Markdown"
        )

        if "ruta_pdf" in context.user_data:
            await update.message.reply_document(
                open(context.user_data["ruta_pdf"], "rb"),
                caption="📄 Cotización completa de tu proyecto"
            )

        await update.message.reply_text(
            "📞 *Habla directamente con un asesor:*\n"
            f"👉 {VENDEDOR_TELEGRAM}\n\n"
            "✅ Proceso finalizado.\n"
            "Escribe *cotizar* para cotizar otra obra.",
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
