from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os

# =========================
# CONFIGURACIÓN
# =========================
TOKEN = os.environ["BOT_TOKEN"]

BASE_COST = 7000  # MXN por m2

EQUIPAMIENTO = {
    "basico": 0,
    "intermedio": 1200,
    "premium": 2500
}

# =========================
# BOT LOGIC
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

    # iniciar cotización
    if texto == "cotizar":
        context.user_data.clear()
        await update.message.reply_text(
            "📐 ¿Cuántos metros cuadrados tendrá la nave?"
        )
        return

    # Paso 1: m2
    if "m2" not in context.user_data:
        try:
            context.user_data["m2"] = float(texto)
            await update.message.reply_text(
                "🏗️ ¿Cuál será la altura libre en metros?"
            )
        except:
            await update.message.reply_text(
                "⚠️ Ingresa solo números. Ejemplo: 2000"
            )
        return

    # Paso 2: altura
    if "altura" not in context.user_data:
        try:
            context.user_data["altura"] = float(texto)
            await update.message.reply_text(
                "📍 ¿En qué estado se construirá?\n"
                "Ejemplo: Jalisco, Querétaro, Nuevo León"
            )
        except:
            await update.message.reply_text(
                "⚠️ Ingresa un número válido para la altura."
            )
        return

    # Paso 3: estado
    if "estado" not in context.user_data:
        context.user_data["estado"] = texto
        await update.message.reply_text(
            "⚙️ ¿Qué nivel de equipamiento deseas?\n"
            "Basico / Intermedio / Premium"
        )
        return

    # Paso 4: equipamiento y cálculo
    if "equipamiento" not in context.user_data:
        equipamiento = texto

        if equipamiento not in EQUIPAMIENTO:
            await update.message.reply_text(
                "⚠️ Elige una opción válida:\n"
                "Basico / Intermedio / Premium"
            )
            return

        context.user_data["equipamiento"] = equipamiento

        m2 = context.user_data["m2"]
        altura = context.user_data["altura"]
        estado = context.user_data["estado"]

        # cálculo del costo
        costo_m2 = BASE_COST

        if altura >= 10:
            costo_m2 += 800

        if estado in ["nuevo león", "cdmx"]:
            costo_m2 += 600

        costo_m2 += EQUIPAMIENTO[equipamiento]

        minimo = m2 * costo_m2
        maximo = minimo * 1.12

        await update.message.reply_text(
            "📐 *Cotización preliminar*\n\n"
            f"• Superficie: {m2:,.0f} m²\n"
            f"• Altura: {altura} m\n"
            f"• Estado: {estado.title()}\n"
            f"• Equipamiento: {equipamiento.title()}\n\n"
            f"💰 *Inversión estimada:*\n"
            f"${minimo:,.0f} – ${maximo:,.0f} MXN\n\n"
            "⚠️ Estimación preliminar.\n\n"
            "👉 Escribe *cotizar* para una nueva cotización.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "Escribe *cotizar* para iniciar una nueva cotización."
    )

# =========================
# RUN BOT
# =========================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))
app.run_polling()
