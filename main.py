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
            "Normativa industrial avanzada"
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

    if texto == "/start":
        context.user_data.clear()
        await update.message.reply_text(
            "👷‍♂️ *Cotizador de Naves Industriales*\n\nEscribe *cotizar* para iniciar.",
            parse_mode="Markdown"
        )
        return

    if texto == "cotizar":
        context.user_data.clear()
        await update.message.reply_text("📐 ¿Cuántos m² tendrá la nave?")
        return

    # ---------- POST COTIZACIÓN ----------
    if context.user_data.get("post_cotizacion") and "tiene_terreno" not in context.user_data:
        if texto in ["si", "sí"]:
            context.user_data["tiene_terreno"] = True
            await update.message.reply_text("📐 Dimensiones del terreno (ej. 30x50)")
        elif texto == "no":
            await update.message.reply_text(f"📞 Contacta a un asesor:\n👉 {VENDEDOR_TELEGRAM}")
            context.user_data.clear()
        return

    if "tiene_terreno" in context.user_data and "dimensiones" not in context.user_data:
        context.user_data["dimensiones"] = texto
        await update.message.reply_text("📍 ¿Estado o ciudad del terreno?")
        return

    if "dimensiones" in context.user_data and "ciudad_proyecto" not in context.user_data:
        context.user_data["ciudad_proyecto"] = texto

        try:
            dim = context.user_data["dimensiones"].replace("mts", "").replace("m", "")
            a, l = dim.split("x")
            m2_terreno = float(a) * float(l)
        except:
            await update.message.reply_text("⚠️ Usa formato correcto: 20x30")
            return

        costo = m2_terreno * PROJECT_COST_M2
        anticipo = costo * ANTICIPO_PORCENTAJE

        await update.message.reply_text(
            "📐 *Proyecto Ejecutivo*\n"
            "• Mecánica de suelos\n"
            "• Cálculo estructural\n"
            "• Planos arquitectónicos\n\n"
            f"📏 Área terreno: {m2_terreno:,.0f} m²\n"
            f"💰 Costo: ${costo:,.0f} MXN\n"
            f"🔻 Anticipo 30%: ${anticipo:,.0f} MXN\n\n"
            f"📞 Asesor:\n👉 {VENDEDOR_TELEGRAM}",
            parse_mode="Markdown"
        )

        if "ruta_pdf" in context.user_data:
            await update.message.reply_document(open(context.user_data["ruta_pdf"], "rb"))

        context.user_data.clear()
        return

    # ---------- COTIZACIÓN ----------
    if "m2" not in context.user_data:
        try:
            context.user_data["m2"] = float(texto)
            await update.message.reply_text("🏗️ Altura libre (m)?")
        except:
            await update.message.reply_text("⚠️ Número inválido")
        return

    if "altura" not in context.user_data:
        try:
            context.user_data["altura"] = float(texto)
            await update.message.reply_text("📍 Estado de construcción?")
        except:
            await update.message.reply_text("⚠️ Altura inválida")
        return

    if "estado" not in context.user_data:
        context.user_data["estado"] = texto
        await update.message.reply_text("🟢 Basico\n🟡 Intermedio\n🔴 Premium")
        return

    if "equipamiento" not in context.user_data:
        if texto not in EQUIPAMIENTO:
            await update.message.reply_text("⚠️ Opción inválida")
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

        await update.message.reply_text(
            f"💰 *Cotización:* ${minimo:,.0f} – ${maximo:,.0f} MXN",
            parse_mode="Markdown"
        )
        await update.message.reply_document(open(ruta, "rb"))

        context.user_data["post_cotizacion"] = True
        await update.message.reply_text(
            "👉 *Cotiza tu proyecto ejecutivo*\n¿Ya cuentas con el terreno?\nResponde: Sí / No",
            parse_mode="Markdown"
        )
        return

# =========================
# RUN
# =========================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))
app.run_polling()
