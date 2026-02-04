from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os, tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

TOKEN = os.environ["BOT_TOKEN"]

BASE_COST = 7000
PROJECT_COST_M2 = 140
ANTICIPO = 0.30

VENDEDOR_TELEGRAM = (
    "https://t.me/ventas_dosp?"
    "text=Hola%20vengo%20del%20cotizador%20de%20naves%20industriales"
)

EQUIPAMIENTO = {
    "básico": {
        "costo": 0,
        "desc": [
            "Estructura metálica",
            "Cubierta y fachadas",
            "Piso industrial básico",
            "Instalación eléctrica básica"
        ]
    },
    "intermedio": {
        "costo": 1200,
        "desc": [
            "Estructura reforzada",
            "Piso alta resistencia",
            "Iluminación LED",
            "Oficinas administrativas"
        ]
    },
    "premium": {
        "costo": 2500,
        "desc": [
            "HVAC",
            "Sprinklers",
            "Iluminación especializada",
            "Oficinas equipadas"
        ]
    }
}

def generar_pdf(datos):
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(f.name, pagesize=letter)
    y = 750

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Cotización Nave Industrial")
    y -= 30

    for k, v in datos.items():
        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"{k}: {v}")
        y -= 18

    c.showPage()
    c.save()
    return f.name

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower().strip()

    # INICIO
    if texto == "/start":
        context.user_data.clear()
        context.user_data["step"] = "NAVE_M2"
        await update.message.reply_text("📐 ¿Cuántos m² tendrá la nave?")
        return

    if texto == "cotizar":
        context.user_data.clear()
        context.user_data["step"] = "NAVE_M2"
        await update.message.reply_text("📐 ¿Cuántos m² tendrá la nave?")
        return

    step = context.user_data.get("step")

    # ===== COTIZACIÓN NAVE =====
    if step == "NAVE_M2":
        context.user_data["m2"] = float(texto)
        context.user_data["step"] = "NAVE_ALTURA"
        await update.message.reply_text("🏗️ ¿Altura libre (m)?")
        return

    if step == "NAVE_ALTURA":
        context.user_data["altura"] = float(texto)
        context.user_data["step"] = "NAVE_ESTADO"
        await update.message.reply_text("📍 ¿Estado de construcción?")
        return

    if step == "NAVE_ESTADO":
        context.user_data["estado_nave"] = texto
        context.user_data["step"] = "NAVE_EQUIPAMIENTO"
        await update.message.reply_text("🟢 Basico\n🟡 Intermedio\n🔴 Premium")
        return

    if step == "NAVE_EQUIPAMIENTO":
        if texto not in EQUIPAMIENTO:
            await update.message.reply_text("Elige: Basico / Intermedio / Premium")
            return

        eq = EQUIPAMIENTO[texto]
        m2 = context.user_data["m2"]
        costo_m2 = BASE_COST + eq["costo"]
        total = m2 * costo_m2

        desglose = "\n".join(f"• {i}" for i in eq["desc"])

        await update.message.reply_text(
            f"📐 Cotización {texto.title()}\n\n"
            f"{desglose}\n\n"
            f"💰 ${total:,.0f} MXN"
        )

        ruta = generar_pdf({"m2": m2, "total": total})
        await update.message.reply_document(open(ruta, "rb"))

        context.user_data["step"] = "PROY_TERRENO"
        await update.message.reply_text("👉 ¿Ya cuentas con el terreno? (Sí / No)")
        return

    # ===== PROYECTO EJECUTIVO =====
    if step == "PROY_TERRENO":
        if texto == "si":
            context.user_data["step"] = "PROY_DIM"
            await update.message.reply_text("📐 Dimensiones del terreno (ej. 30x50)")
        else:
            await update.message.reply_text(f"📞 Asesor:\n👉 {VENDEDOR_TELEGRAM}")
            context.user_data.clear()
        return

    if step == "PROY_DIM":
        context.user_data["dim"] = texto
        context.user_data["step"] = "PROY_CIUDAD"
        await update.message.reply_text("📍 Ciudad o estado del terreno")
        return

    if step == "PROY_CIUDAD":
        a, l = context.user_data["dim"].split("x")
        m2_t = float(a) * float(l)
        costo = m2_t * PROJECT_COST_M2
        anticipo = costo * ANTICIPO

        await update.message.reply_text(
            f"📐 Proyecto Ejecutivo\n"
            f"Área: {m2_t:,.0f} m²\n"
            f"Costo: ${costo:,.0f}\n"
            f"Anticipo: ${anticipo:,.0f}\n\n"
            f"👉 {VENDEDOR_TELEGRAM}"
        )

        context.user_data.clear()
        return

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))
app.run_polling()
