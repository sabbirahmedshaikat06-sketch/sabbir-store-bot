import os
import sqlite3
import random
from datetime import datetime, timedelta, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# BOT SETTINGS
# =========================

BOT_TOKEN = "8582373095:AAGeQvHEQm4sGNqhWx013MFNdIxFBTZUWCc"

# এখানে তোমার Telegram numeric ID বসাও
ADMIN_IDS = [8752830051]

SUPPORT = "@sabbirahmed187"

BIKASH = "01755196906"
NAGAD = "01706965471"

GROUP_LINK = "https://t.me/JibonModsShop"
BOT_LINK = "https://t.me/JibonModsShopbot"

# =========================
# PRODUCTS
# =========================

PRODUCTS = {
    "pro": "SABBIR MOD PRO APK",
    "pest": "PEST TOURNAMENT LOCATION",
    "pink": "PINK TOURNAMENT LOCATION",
    "yellow": "YELLOW TOURNAMENT LOCATION",
    "blue": "BLUE TOURNAMENT LOCATION",
    "green": "GREEN TOURNAMENT LOCATION"
}

DURATIONS = {
    "7": 7,
    "15": 15,
    "30": 30
}

# এখানে তোমার দাম বসাবে
PRICES = {
    "pro": {
        "7": 0,
        "15": 0,
        "30": 0
    },
    "pest": {
        "7": 0,
        "15": 0,
        "30": 0
    },
    "pink": {
        "7": 0,
        "15": 0,
        "30": 0
    },
    "yellow": {
        "7": 0,
        "15": 0,
        "30": 0
    },
    "blue": {
        "7": 0,
        "15": 0,
        "30": 0
    },
    "green": {
        "7": 0,
        "15": 0,
        "30": 0
    }
}

# =========================
# DATABASE
# =========================

DB = "shop.db"


def database():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    con.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product TEXT,
        duration TEXT,
        price INTEGER,
        payment TEXT,
        trx TEXT,
        status TEXT DEFAULT 'pending',
        created TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS credentials(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        duration TEXT,
        active INTEGER DEFAULT 1,
        expires TEXT
    )
    """)

    con.commit()
    return con


def save_user(user):
    con = database()

    con.execute(
        "INSERT OR REPLACE INTO users(id, username) VALUES(?, ?)",
        (user.id, user.username or "")
    )

    con.commit()
    con.close()


def is_admin(user_id):
    return user_id in ADMIN_IDS


# =========================
# KEYBOARD
# =========================

def main_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔐 SABBIR MOD PRO APK",
                callback_data="product:pro"
            )
        ],
        [
            InlineKeyboardButton(
                "🟥 PEST LOCATION",
                callback_data="product:pest"
            )
        ],
        [
            InlineKeyboardButton(
                "🌸 PINK LOCATION",
                callback_data="product:pink"
            )
        ],
        [
            InlineKeyboardButton(
                "🟨 YELLOW LOCATION",
                callback_data="product:yellow"
            )
        ],
        [
            InlineKeyboardButton(
                "🔵 BLUE LOCATION",
                callback_data="product:blue"
            )
        ],
        [
            InlineKeyboardButton(
                "🟢 GREEN LOCATION",
                callback_data="product:green"
            )
        ],
        [
            InlineKeyboardButton(
                "🎰 LUCKY SPIN",
                callback_data="spin"
            )
        ],
        [
            InlineKeyboardButton(
                "🆘 SUPPORT",
                url="https://t.me/sabbirahmed187"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 OFFICIAL GROUP",
                url=GROUP_LINK
            )
        ]
    ])


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    text = """
🛒 SABBIR MODZ SHOP

━━━━━━━━━━━━━━━━━━

🔥 Welcome To SABBIR MODZ SHOP

📦 আমাদের Available Products:

🔐 SABBIR MOD PRO APK
🟥 PEST TOURNAMENT LOCATION
🌸 PINK TOURNAMENT LOCATION
🟨 YELLOW TOURNAMENT LOCATION
🔵 BLUE TOURNAMENT LOCATION
🟢 GREEN TOURNAMENT LOCATION

👇 আপনার প্রয়োজনীয় Product Select করুন।
"""

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard()
    )


# =========================
# PRODUCT
# =========================

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    product_id = query.data.split(":")[1]

    name = PRODUCTS[product_id]

    buttons = []

    for duration in ["7", "15", "30"]:

        price = PRICES[product_id][duration]

        buttons.append([
            InlineKeyboardButton(
                f"📅 {duration} Days — ৳{price}",
                callback_data=f"duration:{product_id}:{duration}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "⬅️ BACK",
            callback_data="home"
        )
    ])

    await query.edit_message_text(
        f"""
📦 PRODUCT

{name}

━━━━━━━━━━━━━━━━━━

⏳ Duration Select করুন:
""",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =========================
# DURATION
# =========================

async def duration(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    _, product_id, days = query.data.split(":")

    price = PRICES[product_id][days]

    context.user_data["product"] = product_id
    context.user_data["duration"] = days
    context.user_data["price"] = price

    await query.edit_message_text(
        f"""
🧾 ORDER DETAILS

📦 Product:
{PRODUCTS[product_id]}

⏳ Duration:
{days} Days

💰 Price:
৳{price}

━━━━━━━━━━━━━━━━━━

Payment Method Select করুন:
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💚 BIKASH",
                    callback_data="payment:bikash"
                )
            ],
            [
                InlineKeyboardButton(
                    "🟠 NAGAD",
                    callback_data="payment:nagad"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ BACK",
                    callback_data=f"product:{product_id}"
                )
            ]
        ])
    )


# =========================
# PAYMENT
# =========================

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    method = query.data.split(":")[1]

    if method == "bikash":
        number = BIKASH
        method_name = "BIKASH"

    else:
        number = NAGAD
        method_name = "NAGAD"

    context.user_data["payment"] = method

    await query.edit_message_text(
        f"""
💳 {method_name} PAYMENT

━━━━━━━━━━━━━━━━━━

📱 Send Money Number:

`{number}`

━━━━━━━━━━━━━━━━━━

💰 আপনার Order Amount অনুযায়ী টাকা পাঠান।

তারপর নিচে আপনার
Transaction ID পাঠান।

Example:

TXN123456789
""",
        parse_mode="Markdown"
    )

    context.user_data["waiting_trx"] = True


# =========================
# TRANSACTION
# =========================

async def transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("waiting_trx"):
        return

    product_id = context.user_data.get("product")
    duration = context.user_data.get("duration")
    price = context.user_data.get("price")
    payment_method = context.user_data.get("payment")

    if not product_id:
        return

    trx = update.message.text.strip()

    save_user(update.effective_user)

    con = database()

    cur = con.execute(
        """
        INSERT INTO orders
        (user_id, product, duration, price, payment, trx, status, created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            update.effective_user.id,
            product_id,
            duration,
            price,
            payment_method,
            trx,
            "pending",
            datetime.now(timezone.utc).isoformat()
        )
    )

    order_id = cur.lastrowid

    con.commit()
    con.close()

    context.user_data.clear()

    admin_text = f"""
🔔 NEW PAYMENT REQUEST

━━━━━━━━━━━━━━━━━━

🆔 Order ID:
#{order_id}

👤 User ID:
{update.effective_user.id}

📦 Product:
{PRODUCTS[product_id]}

⏳ Duration:
{duration} Days

💰 Amount:
৳{price}

💳 Payment:
{payment_method.upper()}

🧾 Transaction:
{trx}
"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ ACCEPT",
                callback_data=f"accept:{order_id}"
            ),
            InlineKeyboardButton(
                "❌ REJECT",
                callback_data=f"reject:{order_id}"
            )
        ]
    ])

    for admin in ADMIN_IDS:

        try:

            await context.bot.send_message(
                admin,
                admin_text,
                reply_markup=keyboard
            )

        except Exception as e:

            print(e)

    await update.message.reply_text(
        """
✅ PAYMENT SUBMITTED

আপনার Transaction ID Admin-এর কাছে পাঠানো হয়েছে।

Admin Payment Verify করার পর
আপনার Product দেওয়া হবে।

🆘 Support:
@sabbirahmed187
"""
    )


# =========================
# ADMIN ACCEPT / REJECT
# =========================

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):

        await query.answer(
            "❌ You are not Admin.",
            show_alert=True
        )

        return

    action, order_id = query.data.split(":")

    con = database()

    order = con.execute(
        "SELECT * FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()

    if not order:

        await query.edit_message_text(
            "❌ Order not found."
        )

        con.close()
        return

    if order["status"] != "pending":

        await query.edit_message_text(
            "⚠️ এই Order already processed."
        )

        con.close()
        return

    # =========================
    # REJECT
    # =========================

    if action == "reject":

        con.execute(
            "UPDATE orders SET status='rejected' WHERE id=?",
            (order_id,)
        )

        con.commit()
        con.close()

        await query.edit_message_text(
            f"❌ Order #{order_id} Rejected."
        )

        await context.bot.send_message(
            order["user_id"],
            f"""
❌ PAYMENT REJECTED

Order ID:
#{order_id}

Payment verify হয়নি।

🆘 Support:
{SUPPORT}
"""
        )

        return

    # =========================
    # ACCEPT
    # =========================

    product_id = order["product"]

    # =========================
    # PRO APK
    # =========================

    if product_id == "pro":

        credential = con.execute(
            """
            SELECT *
            FROM credentials
            WHERE duration=?
            AND active=1
            ORDER BY id ASC
            LIMIT 1
            """,
            (order["duration"],)
        ).fetchone()

        if not credential:

            con.close()

            await query.edit_message_text(
                "⚠️ এই Duration-এর কোনো User/Password Stock নেই।"
            )

            return

        expire_time = (
            datetime.now(timezone.utc)
            + timedelta(days=DURATIONS[order["duration"]])
        )

        con.execute(
            """
            UPDATE credentials
            SET active=0,
                expires=?
            WHERE id=?
            """,
            (
                expire_time.isoformat(),
                credential["id"]
            )
        )

        delivery = f"""
🎉 PAYMENT ACCEPTED

━━━━━━━━━━━━━━━━━━

🔐 SABBIR MOD PRO APK

👤 Username:
{credential["username"]}

🔑 Password:
{credential["password"]}

⏳ Duration:
{order["duration"]} Days

🕐 Expires:
{expire_time.strftime("%Y-%m-%d %H:%M UTC")}

━━━━━━━━━━━━━━━━━━

🆘 Support:
{SUPPORT}
"""

        await context.bot.send_message(
            order["user_id"],
            delivery
        )

    # =========================
    # LOCATION FILE
    # =========================

    else:

        filename = f"product_files/{product_id}.bin"

        if not os.path.exists(filename):

            con.close()

            await query.edit_message_text(
                f"""
⚠️ Product File Missing!

GitHub-এ এই file দিতে হবে:

product_files/{product_id}.bin
"""
            )

            return

        await context.bot.send_document(
            order["user_id"],
            document=open(filename, "rb"),
            caption=f"""
🎉 PAYMENT ACCEPTED

📦 {PRODUCTS[product_id]}

⏳ Duration:
{order["duration"]} Days

🆘 Support:
{SUPPORT}
"""
        )

    # Order accepted

    con.execute(
        "UPDATE orders SET status='accepted' WHERE id=?",
        (order_id,)
    )

    con.commit()
    con.close()

    await query.edit_message_text(
        f"✅ Order #{order_id} Accepted & Delivered."
    )


# =========================
# ADD USER/PASSWORD
# =========================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):

        return

    if len(context.args) != 3:

        await update.message.reply_text(
            """
❌ Wrong Format

Use:

/adduser USERNAME PASSWORD DAYS

Example:

/adduser sabbir123 pass123 7

Days:

7
15
30
"""
        )

        return

    username = context.args[0]
    password = context.args[1]
    days = context.args[2]

    if days not in DURATIONS:

        await update.message.reply_text(
            "❌ Days must be 7, 15 or 30."
        )

        return

    con = database()

    con.execute(
        """
        INSERT INTO credentials
        (username, password, duration, active)
        VALUES (?, ?, ?, 1)
        """,
        (
            username,
            password,
            days
        )
    )

    con.commit()
    con.close()

    await update.message.reply_text(
        f"""
✅ USER/PASSWORD ADDED

👤 Username:
{username}

🔑 Password:
{password}

⏳ Duration:
{days} Days
"""
    )


# =========================
# STOCK
# =========================

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    con = database()

    rows = con.execute(
        """
        SELECT duration, COUNT(*) AS total
        FROM credentials
        WHERE active=1
        GROUP BY duration
        """
    ).fetchall()

    con.close()

    text = "📦 PRO APK STOCK\n\n"

    for days in ["7", "15", "30"]:

        count = 0

        for row in rows:

            if row["duration"] == days:
                count = row["total"]

        text += f"⏳ {days} Days: {count}\n"

    await update.message.reply_text(text)


# =========================
# LUCKY SPIN
# =========================

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    prizes = [
        "🎁 Better Luck Next Time!",
        "🎁 5 TK Bonus",
        "🎁 10 TK Bonus",
        "🎁 20 TK Bonus"
    ]

    result = random.choice(prizes)

    await query.edit_message_text(
        f"""
🎰 LUCKY SPIN

━━━━━━━━━━━━━━━━━━

🎉 RESULT:

{result}

━━━━━━━━━━━━━━━━━━

🆘 Support:
{SUPPORT}
"""
    )


# =========================
# HOME
# =========================

async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🛒 SABBIR MODZ SHOP\n\nProduct Select করুন:",
        reply_markup=main_keyboard()
    )


# =========================
# MAIN
# =========================

def main():

    if BOT_TOKEN == "YOUR_BOT_TOKEN":

        print("❌ Please put your BotFather Token in BOT_TOKEN")

        return

    database().close()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("adduser", adduser)
    )

    app.add_handler(
        CommandHandler("stock", stock)
    )

    app.add_handler(
        CallbackQueryHandler(
            product,
            pattern="^product:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            duration,
            pattern="^duration:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            payment,
            pattern="^payment:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern="^(accept|reject):"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            spin,
            pattern="^spin$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            home,
            pattern="^home$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            transaction
        )
    )

    print("SABBIR MODZ SHOP BOT RUNNING...")

    app.run_polling()


if __name__ == "__main__":
    main()
