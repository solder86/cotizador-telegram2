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

BASE_COST = 7000          # MXN por m²
PROJECT_COST_M2 = 140     # Proyecto ejecutivo
ANTICIPO_PORCENTAJE = 0.30

# 👉 Telegram del vendedor CON mensaje de inicio
VENDEDOR_TELEGRAM = (
    "https://t.me/ventas_dosp?"
    "text=Hola%20vengo%20del%20cotizador%20de%20naves%20industriales.%20"
    "Ya%20realic%C3%A9%20una%20cotizaci%C3%B3n%20y%20me%20gustar%C3%ADa%20continuar."
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
            "Iluminación especializada por área",
            "Sistema HVAC",
            "Sistema contra incendios (sprinklers)",
            "Oficinas totalmente equipadas",
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
    width, height = letter
    y = height - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "DOS-P | Innovación Inmobiliaria")
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Arq. Noel Peña")
    y -= 14
    c.drawString(50, y, "Cel. 33 1720 4455")
    y -= 30

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Cotización Preliminar – Nave Industrial")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Superficie: {datos['m2']:,.0f} m²"); y -= 18
    c.drawString(50, y, f"Altura libre: {datos['altura']} m"); y -= 18
    c.drawString(50, y, f"Estado: {datos['estado'].title()}"); y -= 18
    c.drawString(50, y, f"Equipamiento: {datos['equipamiento'].title()}"); y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Incluye:")
    y -= 18

    c.setFont("Helvetica", 11)
    for item in datos["caracteristicas"]:
        c.drawString(60, y, f"- {item}")
        y -= 14

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Inversión estimada:")
    y -= 18

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

    # /start
    if texto == "/start":
        context.user_data.clear()
        await update.message.reply_text(
            "👷‍♂️ *Cotizador de Naves Industriales*\n\n"
            "Escribe *cotizar* para iniciar.",
            parse_mode="Markdown"
        )
        return

    # iniciar
    if texto == "cotizar":
        context.user_data.clear()
        await update.message.reply_text("📐 ¿Cuántos metros cuadrados tendrá la nave?")
        return

    # =========================
    # POST COTIZACIÓN – TERRENO
    # =========================
    if context.user_data.get("post_cotizacion") and "tiene_terreno" not in context.user_data:
        if texto in ["si", "sí"]:
            context.user_data["tiene_terreno"] = True
            await update.message.reply_text(
                "📐 Indica las *dimensiones del terreno*\nEjemplo: 20x30 mts",
                parse_mode="Markdown"
            )
        elif texto == "no":
            if "ruta_pdf" in context.user_data:
                await update.message.reply_document(
                    open(context.user_data["ruta_pdf"], "rb"),
                    filename="Cotizacion_Nave_Industrial_DOS-P.pdf",
                    caption="📄 Cotización preliminar de referencia"
                )

            await update.message.reply_text(
                "📞 Contacta directamente a un asesor:\n"
                f"👉 {VENDEDOR_TELEGRAM}"
            )

            context.user_data.clear()
            await update.message.reply_text(
                "✅ Proceso finalizado.\n\n"
                "Escribe *cotizar* para cotizar otra obra\n"
                "o */start* para reiniciar.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("Responde *Sí* o *No*")
        return

    # DIMENSIONES
    if "tiene_terreno" in context.user_data and "dimensiones" not in context.user_data:
        context.user_data["dimensiones"] = texto
        await update.message.reply_text("📍 ¿En qué estado o ciudad se ubica el terreno?")
        return

    # CIUDAD + PROYECTO EJECUTIVO
    if "dimensiones" in context.user_data and "ciudad_proyecto" not in context.user_data:
        context.user_data["ciudad_proyecto"] = texto

        m2 = context.user_data["m2"]
        costo = m2 * PROJECT_COST_M2
        anticipo = costo * ANTICIPO_PORCENTAJE

        await update.message.reply_text(
            "📐 *Proyecto Ejecutivo Incluye:*\n"
            "• Mecánica de suelos\n"
            "• Cálculo estructural\n"
            "• Planos arquitectónicos\n\n"
            f"💰 *Costo del proyecto:* ${costo:,.0f} MXN\n"
            f"🔻 *Anticipo 30%:* ${anticipo:,.0f} MXN\n\n"
            "📞 Contacta directamente a un asesor:\n"
            f"👉 {VENDEDOR_TELEGRAM}",
            parse_mode="Markdown"
        )

        if "ruta_pdf" in context.user_data:
            await update.message.reply_document(
                open(context.user_data["ruta_pdf"], "rb"),
                filename="Cotizacion_Nave_Industrial_DOS-P.pdf",
                caption="📄 Cotización preliminar de tu proyecto"
            )

        context.user_data.clear()
        await update.message.reply_text(
            "✅ Proceso finalizado.\n\n"
            "Escribe *cotizar* para cotizar otra obra\n"
            "o */start* para reiniciar.",
            parse_mode="Markdown"
        )
        return

    # =========================
    # COTIZACIÓN DE NAVE
    # =========================
    if "m2" not in context.user_data:
        try:
            m2 = float(texto)
            if m2 <= 0:
                raise ValueError
            context.user_data["m2"] = m2
            await update.message.reply_text("🏗️ ¿Altura libre en metros?")
        except:
            await update.message.reply_text("⚠️ Ingresa un número válido.")
        return

    if "altura" not in context.user_data:
        try:
            altura = float(texto)
            if altura < 4 or altura > 20:
                raise ValueError
            context.user_data["altura"] = altura
            await update.message.reply_text("📍 ¿En qué estado se construirá?")
        except:
            await update.message.reply_text("⚠️ Altura inválida.")
        return

    if "estado" not in context.user_data:
        context.user_data["estado"] = texto
        await update.message.reply_text(
            "⚙️ Nivel de equipamiento:\n\n"
            "🟢 Basico\n🟡 Intermedio\n🔴 Premium\n\n"
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
        equip = texto

        costo_m2 = BASE_COST
        if altura >= 10:
            costo_m2 += 800
        if estado in ["nuevo león", "cdmx"]:
            costo_m2 += 600
        costo_m2 += EQUIPAMIENTO[equip]["costo"]

        minimo = m2 * costo_m2
        maximo = minimo * 1.12

        await update.message.reply_text(
            f"📐 *Cotización preliminar*\n\n"
            f"💰 ${minimo:,.0f} – ${maximo:,.0f} MXN",
            parse_mode="Markdown"
        )

        datos_pdf = {
            "m2": m2,
            "altura": altura,
            "estado": estado,
            "equipamiento": equip,
            "caracteristicas": EQUIPAMIENTO[equip]["descripcion"],
            "minimo": minimo,
            "maximo": maximo
        }

        ruta = generar_pdf(datos_pdf)
        context.user_data["ruta_pdf"] = ruta

        await update.message.reply_document(
            open(ruta, "rb"),
            filename="Cotizacion_Nave_Industrial_DOS-P.pdf"
        )

        context.user_data["post_cotizacion"] = True
        await update.message.reply_text(
            "👉 *Cotiza tu proyecto ejecutivo para arrancar números reales*\n\n"
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
