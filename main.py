# bot_buy_updated.py
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.sync_api import sync_playwright
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=1)

TOKEN = "8503785532:AAEdPuukngcv3pdkMlf4pOWiQTC-iGYWzro"
SHOP_URL = "https://bloxfruitshop.shop/"  # главная страница с товарами

# ---------------- Функция покупки ----------------
def buy_item(target_item: str) -> str:
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )

            context = browser.new_context(storage_state="state.json")
            page = context.new_page()

            page.goto("https://bloxfruitshop.shop/")
            page.wait_for_timeout(5000)

            for attempt in range(1, 4):  # 🔁 3 попытки
                prev_count = 0

                # ⬇️ Скроллим до конца страницы
                while True:
                    cards = page.query_selector_all(".feature-card")
                    if len(cards) == prev_count:
                        break

                    prev_count = len(cards)
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(2000)

                # 🔍 Ищем товар
                cards = page.query_selector_all(".feature-card")

                for card in cards:
                    classes = card.get_attribute("class") or ""
                    if "product-disable" in classes:
                        continue

                    title_elem = card.query_selector(".feature-name")
                    if not title_elem:
                        continue

                    title = title_elem.inner_text().strip()

                    # ✅ Поиск по одному слову
                    if target_item.lower() not in title.lower():
                        continue

                    buy_btn_card = card.query_selector("button.btn-buy")
                    if not buy_btn_card:
                        continue

                    buy_btn_card.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    buy_btn_card.click()

                    page.wait_for_timeout(2000)

                    buy_btn = page.query_selector("button#btnBuy")
                    if buy_btn:
                        buy_btn.click()
                        browser.close()
                        return f"✅ Покупка выполнена: {title}"

                # ⏳ Если не нашли — ждём и пробуем ещё раз
                page.wait_for_timeout(3000)

            browser.close()
            return f"❌ Товар '{target_item}' не найден после 3 попыток"

    except Exception as e:
        return f"⚠️ Ошибка при покупке: {e}"






# ---------------- Telegram бот ----------------
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Используй: /buy <название товара>")
        return

    item_name = " ".join(context.args)
    await update.message.reply_text(f"🛒 Пытаюсь купить: {item_name}...")

    # Запускаем синхронный buy_item в отдельном потоке
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, buy_item, item_name)

    await update.message.reply_text(result)

# ---------------- Запуск бота ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("buy", buy))
    print("Бот запущен...")
    app.run_polling()
