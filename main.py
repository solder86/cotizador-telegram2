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

BASE_COST = 7000  # MXN por m²

EQUIPAMIENTO = {
    "basico": {
        "costo": 0,
        "descripcion": [
            "Estructura metálica",
            "Cubierta y fachadas",
            "Piso industrial básico",
            "Instalación eléctrica mínima",
            "Preparación para ampliaciones"
        ]
    },
    "intermedio": {
        "costo": 1200,
        "descripcion": [
            "Todo lo básico",
            "Andenes de carga",
            "Oficinas administrativas",
            "Iluminación LED industrial",
            "Instalación eléctrica industrial",
            "Piso de mayor capacidad"
        ]
    },
    "premium": {
        "costo": 2500,
        "descripcion": [
            "Todo lo intermedio",
            "HVAC",
            "Sistema contra incendios (sprinklers)",
            "Iluminación especializada",
            "Oficinas equipadas",
            "Normativa avanzada"
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

    # Encabezado empresa
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "DOS-P | Innovación Inmobiliaria")
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Arq. Giovanni Peña Camacho")
    y -= 14
    c.drawString(50, y, "Cel. 33 1720 4455")
    y -= 30

    # Título
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Cotización Preliminar – Nave Industrial")
    y -= 30

    # Datos
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Superficie: {datos['m2']:,.0f} m²"); y -= 18
    c.drawString(50, y, f"Altura libre: {datos['altura']} m"); y -= 18
    c.drawString(50, y, f"Estado: {datos['estado'].title()}"); y -= 18
    c.drawString(50, y, f"Equipamiento: {datos['equipamiento'].title()}"); y -= 25

    # Incluye
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Incluye:")
    y -= 18

    c.setFont("Helvetica", 11)
    for item in datos["caracteristicas"]:
        c.drawString(60, y, f"- {item}")
        y -= 14

    y -= 20

    # Inversión
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Inversión estimada:")
    y -= 18

    c.setFont("Helvetica", 11)
    c.drawString(
        50, y,
        f"${datos['minimo']:,.0f} – ${datos['maximo']:,.0f} MXN"
    )
    y -= 30

    # Nota legal
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        50, y,
        "Esta cotización es preliminar y no constituye una oferta contractual."
    )

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
            "👷‍♂️ Bienvenido al *Cotizador de Naves Industriales*\n\n"
            "Escribe *cotizar* para iniciar.",
            parse_mode="Markdown"
        )
        return

    # iniciar
    if texto == "cotizar":
        context.user_data.clear()
        await update.message.reply_text(
            "📐 ¿Cuántos metros cuadrados tendrá la nave?"
        )
        return

    # PASO 1: m2
    if "m2" not in context.user_data:
        try:
            m2 = float(texto)
            if m2 <= 0:
                raise ValueError
            context.user_data["m2"] = m2
            await update.message.reply_text(
                "🏗️ ¿Cuál será la *altura libre* en metros? (Ej. 9)"
            )
        except:
            await update.message.reply_text(
                "⚠️ Ingresa un número válido de m². Ejemplo: 2000"
            )
        return

    # PASO 2: altura
    if "altura" not in context.user_data:
        try:
            altura = float(texto)
            if altura < 4 or altura > 20:
                raise ValueError
            context.user_data["altura"] = altura
            await update.message.reply_text(
                "📍 ¿En qué estado se construirá?\n"
                "Ejemplo: Jalisco, Querétaro, Nuevo León"
            )
        except:
            await update.message.reply_text(
                "⚠️ Ingresa una altura válida (entre 4 y 20 m)."
            )
        return

    # PASO 3: estado
    if "estado" not in context.user_data:
        context.user_data["estado"] = texto
        await update.message.reply_text(
            "⚙️ ¿Qué nivel de equipamiento deseas?\n\n"
            "🟢 Basico\n"
            "🟡 Intermedio\n"
            "🔴 Premium\n\n"
            "Escribe: Basico / Intermedio / Premium"
        )
        return

    # PASO 4: equipamiento + cálculo
    if "equipamiento" not in context.user_data:
        if texto not in EQUIPAMIENTO:
            await update.message.reply_text(
                "⚠️ Opción no válida.\n"
                "Escribe: Basico / Intermedio / Premium"
            )
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

        caracteristicas = "\n".join(
            f"• {item}" for item in EQUIPAMIENTO[equip]["descripcion"]
        )

        await update.message.reply_text(
            "📐 *Cotización preliminar*\n\n"
            f"• Superficie: {m2:,.0f} m²\n"
            f"• Altura: {altura} m\n"
            f"• Estado: {estado.title()}\n"
            f"• Equipamiento: {equip.title()}\n\n"
            "Incluye:\n"
            f"{caracteristicas}\n\n"
            f"💰 *Inversión estimada:*\n"
            f"${minimo:,.0f} – ${maximo:,.0f} MXN\n\n"
            "⚠️ Estimación preliminar.",
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

        ruta_pdf = generar_pdf(datos_pdf)

        await update.message.reply_document(
            document=open(ruta_pdf, "rb"),
            filename="Cotizacion_Nave_Industrial_DOS-P.pdf",
            caption="📄 Cotización preliminar – DOS-P Innovación Inmobiliaria"
        )

        # 🔄 RESET DEL FLUJO
        context.user_data.clear()

        await update.message.reply_text(
            "✅ Cotización finalizada.\n\n"
            "Escribe *cotizar* para una nueva cotización\n"
            "o */start* para reiniciar.",
            parse_mode="Markdown"
        )
        return

# =========================
# RUN
# =========================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))
app.run_polling()
