from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# =========================
# CONFIGURACIÓN
# =========================
TOKEN = os.environ["BOT_TOKEN"]

BASE_COST = 7000
PROJECT_COST_M2 = 140
ANTICIPO_PORCENTAJE = 0.30

VENDEDOR_TELEGRAM = (
    "https://t.me/ventas_dosp?"
    "text=Hola%20vengo%20del%20cotizador%20de%20naves%20industriales."
)

EQUIPAMIENTO = {
    "basico": {
        "costo": 0,
        "descripcion": [
            "Estructura metálica principal",
            "Cubierta y fachadas de lámina",
            "Piso industrial de concreto estándar",
            "Instalación eléctrica básica",
            "Preparación para futuras ampliaciones"
        ]
    },
    "intermedio": {
        "costo": 1200,
        "descripcion": [
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
        "descripcion": [
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
    archivo = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(archivo.name, pagesize=letter)
    y = letter[1] - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "DOS-P | Innovación Inmobiliaria")
    y -= 25

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
    for item in datos["caracteristicas"]:
        c.drawString(60, y, f"- {item}")
        y -= 14

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Inversión estimada:")
    y -= 16

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"${datos['minimo']:,.0f} – ${datos['maximo']:,.0f} MXN")

    y -= 30
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, y, "Cotización preliminar, no contractual.")

    c.showPage()
    c.save()
    return archivo.name

# =========================
# BOT
# =========================
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower().strip()

    # =========================
    # PROYECTO EJECUTIVO (PRIORIDAD)
    # =========================
    if context.user_data.get("post_cotizacion"):

        if "tiene_terreno" not in context.user_data:
            if texto in ["si", "sí"]:
                context.user_data["tiene_terreno"] = True
                await update.message.reply_text(
                    "📐 Indica las dimensiones del terreno\nEjemplo: 30x50"
                )
            elif texto == "no":
                await update.message.reply_text(
                    "📞 Contacta a un asesor:\n"
                    f"👉 {VENDEDOR_TELEGRAM}"
                )
                context.user_data.clear()
            else:
                await update.message.reply_text("Responde *Sí* o *No*")
            return

        if "dimensiones" not in context.user_data:
            context.user_data["dimensiones"] = texto
            await update.message.reply_text(
                "📍 ¿En qué estado o ciudad se ubica el terreno?"
            )
            return

        if "ciudad_proyecto" not in context.user_data:
            context.user_data["ciudad_proyecto"] = texto

            try:
                dim = context.user_data["dimensiones"].replace("mts", "").replace("m", "")
                a, l = dim.split("x")
                m2_terreno = float(a) * float(l)
            except:
                await update.message.reply_text("⚠️ Usa formato: 20x30")
                return

            costo = m2_terreno * PROJECT_COST_M2
            anticipo = costo * ANTICIPO_PORCENTAJE

            await update.message.reply_text(
                "📐 *Proyecto Ejecutivo Incluye:*\n"
                "• Mecánica de suelos\n"
                "• Cálculo estructural\n"
                "• Planos arquitectónicos\n\n"
                f"📏 *Área del terreno:* {m2_terreno:,.0f} m²\n"
                f"💰 *Costo del proyecto:* ${costo:,.0f} MXN\n"
                f"🔻 *Anticipo 30%:* ${anticipo:,.0f} MXN\n\n"
                "📞 Contacta a un asesor:\n"
                f"👉 {VENDEDOR_TELEGRAM}",
                parse_mode="Markdown"
            )

            if "ruta_pdf" in context.user_data:
                await update.message.reply_document(
                    open(context.user_data["ruta_pdf"], "rb")
                )

            context.user_data.clear()
            return

    # =========================
    # INICIO
    # =========================
    if texto == "/start":
        context.user_data.clear()
        await update.message.reply_text(
            "👷‍♂️ *Cotizador de Naves Industriales*\n\n"
            "Escribe *cotizar* para iniciar.",
            parse_mode="Markdown"
        )
        return

    if texto == "cotizar":
        context.user_data.clear()
        await update.message.reply_text("📐 ¿Cuántos m² tendrá la nave?")
        return

    # =========================
    # COTIZACIÓN DE NAVE
    # =========================
    if "m2" not in context.user_data:
        try:
            context.user_data["m2"] = float(texto)
            await update.message.reply_text("🏗️ ¿Altura libre en metros?")
        except:
            await update.message.reply_text("⚠️ Ingresa un número válido.")
        return

    if "altura" not in context.user_data:
        try:
            context.user_data["altura"] = float(texto)
            await update.message.reply_text("📍 ¿En qué estado se construirá?")
        except:
            await update.message.reply_text("⚠️ Altura inválida.")
        return

    if "estado" not in context.user_data:
        context.user_data["estado"] = texto
        await update.message.reply_text(
            "⚙️ Nivel de equipamiento:\n\n"
            "🟢 Basico\n"
            "🟡 Intermedio\n"
            "🔴 Premium\n\n"
            "Escribe: Basico / Intermedio / Premium"
        )
        return

    if "equipamiento" not in context.user_data:
        if texto not in EQUIPAMIENTO:
            await update.message.reply_text("⚠️ Opción no válida.")
            return

        context.user_data["equipamiento"] = texto

        m2 = context.user_data["m2"]
        altura = context.user_data["altura"]
        estado = context.user_data["estado"]

        costo_m2 = BASE_COST + EQUIPAMIENTO[texto]["costo"]
        if altura >= 10:
            costo_m2 += 800
        if estado in ["jalisco", "cdmx", "nuevo león"]:
            costo_m2 += 600

        minimo = m2 * costo_m2
        maximo = minimo * 1.12

        caracteristicas_texto = "\n".join(
            f"• {item}" for item in EQUIPAMIENTO[texto]["descripcion"]
        )

        await update.message.reply_text(
            "📐 *Cotización preliminar*\n\n"
            f"🏗️ *Nivel:* {texto.title()}\n\n"
            "*Incluye:*\n"
            f"{caracteristicas_texto}\n\n"
            f"💰 *Inversión estimada:*\n"
            f"${minimo:,.0f} – ${maximo:,.0f} MXN\n\n"
            "📄 Te comparto el PDF con el detalle completo.",
            parse_mode="Markdown"
        )

        datos_pdf = {
            "m2": m2,
            "altura": altura,
            "estado": estado,
            "equipamiento": texto,
            "caracteristicas": EQUIPAMIENTO[texto]["descripcion"],
            "minimo": minimo,
            "maximo": maximo
        }

        ruta = generar_pdf(datos_pdf)
        context.user_data["ruta_pdf"] = ruta

        await update.message.reply_document(open(ruta, "rb"))

        context.user_data["post_cotizacion"] = True
        await update.message.reply_text(
            "👉 *Cotiza tu proyecto ejecutivo*\n\n"
            "¿Ya cuentas con el terreno?\nResponde: *Sí* o *No*",
            parse_mode="Markdown"
        )
        return

# =========================
# RUN
# =========================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))
app.run_polling()
