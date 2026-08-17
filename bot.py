import os
import sqlite3
import random
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("8582373095:AAGeQvHEQm4sGNqhWx013MFNdIxFBTZUWCc")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8752830051"))

SHOP_NAME = "SABBIR MODZ SHOP"

SUPPORT = "@sabbirahmed187"

BKASH = "01755196906"
NAGAD = "01706965471"

DB_FILE = "shop.db"


# =========================================================
# PRODUCTS
# =========================================================

PRODUCTS = {
    "sabbir_pro_7": {
        "name": "SABBIR MOD PRO APK - 7 DAY",
        "price": 40,
        "type": "credential",
        "duration": 7,
    },
    "sabbir_pro_15": {
        "name": "SABBIR MOD PRO APK - 15 DAY",
        "price": 80,
        "type": "credential",
        "duration": 15,
    },
    "sabbir_pro_30": {
        "name": "SABBIR MOD PRO APK - 30 DAY",
        "price": 120,
        "type": "credential",
        "duration": 30,
    },

    "br_cs": {
        "name": "BR CS + TOURNAMENT LOCATION",
        "price": 250,
        "type": "file",
        "file_key": "br_cs",
    },

    "pest": {
        "name": "PEST TOURNAMENT LOCATION 🩵",
        "price": 180,
        "type": "file",
        "file_key": "pest",
    },

    "pink": {
        "name": "PINK TOURNAMENT LOCATION 💜",
        "price": 180,
        "type": "file",
        "file_key": "pink",
    },

    "yellow": {
        "name": "YELLOW TOURNAMENT LOCATION 💛",
        "price": 180,
        "type": "file",
        "file_key": "yellow",
    },

    "blue": {
        "name": "BLUE TOURNAMENT LOCATION 💙",
        "price": 180,
        "type": "file",
        "file_key": "blue",
    },

    "green": {
        "name": "GREEN TOURNAMENT LOCATION 💚",
        "price": 180,
        "type": "file",
        "file_key": "green",
    },
}


# =========================================================
# DATABASE
# =========================================================

def db():
    return sqlite3.connect(DB_FILE)


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        username TEXT,
        balance REAL DEFAULT 0,
        referral_by INTEGER,
        referral_rewarded INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        duration INTEGER,
        sold INTEGER DEFAULT 0,
        sold_to INTEGER,
        sold_at TEXT,
        expires_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        file_key TEXT PRIMARY KEY,
        telegram_file_id TEXT,
        file_name TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_key TEXT,
        product_name TEXT,
        amount REAL,
        payment_method TEXT,
        transaction_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        delivered_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS spins (
        user_id INTEGER,
        spin_date TEXT,
        result INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        payment_method TEXT,
        transaction_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )
    """)

    con.commit()
    con.close()


# =========================================================
# HELPERS
# =========================================================

def now():
    return datetime.now()


def now_str():
    return now().strftime("%Y-%m-%d %H:%M:%S")


def get_user(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return row


def ensure_user(tg_user, referral_by=None):
    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (tg_user.id,)
    )

    exists = cur.fetchone()

    if not exists:
        cur.execute("""
        INSERT INTO users
        (user_id, name, username, balance, referral_by, created_at)
        VALUES (?, ?, ?, 0, ?, ?)
        """, (
            tg_user.id,
            tg_user.full_name,
            tg_user.username or "",
            referral_by,
            now_str()
        ))

    else:
        cur.execute("""
        UPDATE users
        SET name=?, username=?
        WHERE user_id=?
        """, (
            tg_user.full_name,
            tg_user.username or "",
            tg_user.id
        ))

    con.commit()
    con.close()


def add_balance(user_id, amount):
    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET balance=balance+? WHERE user_id=?",
        (amount, user_id)
    )

    con.commit()
    con.close()


def get_balance(user_id):
    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()
    con.close()

    return row[0] if row else 0


def remove_balance(user_id, amount):
    con = db()
    cur = con.cursor()

    cur.execute("""
    UPDATE users
    SET balance=balance-?
    WHERE user_id=? AND balance>=?
    """, (amount, user_id, amount))

    changed = cur.rowcount

    con.commit()
    con.close()

    return changed == 1


def is_admin(user_id):
    return user_id == ADMIN_ID


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton("🛍️ Shop Now", callback_data="shop")
        ],
        [
            InlineKeyboardButton("📦 My Orders", callback_data="orders"),
            InlineKeyboardButton("👤 Profile", callback_data="profile")
        ],
        [
            InlineKeyboardButton("💰 Add Balance", callback_data="add_balance"),
            InlineKeyboardButton("🎁 Referral", callback_data="referral")
        ],
        [
            InlineKeyboardButton("🎰 Lucky Spin", callback_data="spin")
        ],
        [
            InlineKeyboardButton("📁 Download Files", callback_data="downloads")
        ],
        [
            InlineKeyboardButton("📺 Tutorials", callback_data="tutorials"),
            InlineKeyboardButton("🆘 Support", callback_data="support")
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    referral_by = None

    if context.args:
        arg = context.args[0]

        if arg.startswith("ref_"):
            try:
                ref_id = int(arg.replace("ref_", ""))

                if ref_id != user.id:
                    referral_by = ref_id

            except:
                pass

    ensure_user(user, referral_by)

    text = f"""
🏪 — {SHOP_NAME} —

👋 Welcome, {user.first_name}!

⭐ — SHOP FEATURES — ⭐

├ 🔑 Premium Game Keys
├ ⚡ Instant Delivery
├ 🔒 Secure Payment
├ 💰 Best Prices
├ 🎁 Referral Rewards
└ 🏆 Professional Support

━━━━━━━━━━━━━━━━

🚀 Click Shop Now to Start!
"""

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )


# =========================================================
# SHOP
# =========================================================

async def shop(update, context):

    query = update.callback_query
    await query.answer()

    text = """
🛍️ — SABBIR MODZ SHOP —

🔑 SABBIR MOD PRO APK
├ 7 Day — 40 Tk
├ 15 Day — 80 Tk
└ 30 Day — 120 Tk

🎮 TOURNAMENT LOCATION

├ BR CS + TOURNAMENT — 250 Tk / 3 Month
├ PEST 🩵 — 180 Tk / 3 Month
├ PINK 💜 — 180 Tk / 3 Month
├ YELLOW 💛 — 180 Tk / 3 Month
├ BLUE 💙 — 180 Tk / 3 Month
└ GREEN 💚 — 180 Tk / 3 Month
"""

    keyboard = []

    for key, product in PRODUCTS.items():

        keyboard.append([
            InlineKeyboardButton(
                f"🛒 {product['name']} — {product['price']} Tk",
                callback_data=f"product:{key}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("🔙 Back", callback_data="home")
    ])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# PRODUCT
# =========================================================

async def product_select(update, context):

    query = update.callback_query
    await query.answer()

    key = query.data.split(":", 1)[1]

    product = PRODUCTS.get(key)

    if not product:
        return

    context.user_data["selected_product"] = key

    text = f"""
🛒 PRODUCT SELECTED

📦 {product['name']}

💰 Price: {product['price']} Tk

🇧🇩 PAYMENT METHOD
"""

    keyboard = [
        [
            InlineKeyboardButton(
                " bKash",
                callback_data="paymethod:bkash"
            )
        ],
        [
            InlineKeyboardButton(
                " Nagad",
                callback_data="paymethod:nagad"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="shop"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# PAYMENT METHOD
# =========================================================

async def payment_method(update, context):

    query = update.callback_query
    await query.answer()

    method = query.data.split(":")[1]

    product_key = context.user_data.get("selected_product")

    if not product_key:
        await query.edit_message_text(
            "❌ Product not selected.",
            reply_markup=main_menu()
        )
        return

    product = PRODUCTS[product_key]

    if method == "bkash":
        number = BKASH
        name = "bKash"

    else:
        number = NAGAD
        name = "Nagad"

    context.user_data["payment_method"] = method

    text = f"""
💳 PAYMENT INFORMATION

📦 Product:
{product['name']}

💰 Amount:
{product['price']} Tk

🇧🇩 Method:
{name}

📱 Send Money To:
`{number}`

━━━━━━━━━━━━━━━━

💡 টাকা পাঠানোর পর নিচের
"Transaction ID পাঠান" বাটনে চাপুন।

⚠️ Payment verify করার পর Admin
আপনার order accept করবেন।
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "🧾 Transaction ID পাঠান",
                callback_data="send_tx"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="shop"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# SEND TRANSACTION
# =========================================================

async def send_tx(update, context):

    query = update.callback_query
    await query.answer()

    context.user_data["waiting_tx"] = True

    await query.message.reply_text(
        "🧾 আপনার Transaction ID লিখে পাঠান:\n\n"
        "উদাহরণ: `TX123456789`",
        parse_mode=ParseMode.MARKDOWN
    )


async def text_handler(update, context):

    user = update.effective_user
    text = update.message.text.strip()

    ensure_user(user)

    # -----------------------------------------------------
    # ADMIN PENDING INPUT
    # -----------------------------------------------------

    if is_admin(user.id):

        admin_action = context.user_data.get("admin_action")

        if admin_action:

            # Add credential
            if admin_action == "add_credential":

                parts = [x.strip() for x in text.split("|")]

                if len(parts) != 3:
                    await update.message.reply_text(
                        "❌ Format ভুল।\n\n"
                        "এইভাবে পাঠান:\n"
                        "`username | password | 7`\n\n"
                        "Duration: 7 / 15 / 30",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return

                username, password, duration = parts

                try:
                    duration = int(duration)
                except:
                    await update.message.reply_text(
                        "❌ Duration 7, 15 অথবা 30 দিন হতে হবে।"
                    )
                    return

                if duration not in [7, 15, 30]:
                    await update.message.reply_text(
                        "❌ Duration শুধু 7 / 15 / 30 হতে পারে।"
                    )
                    return

                con = db()
                cur = con.cursor()

                cur.execute("""
                INSERT INTO credentials
                (username,password,duration)
                VALUES (?,?,?)
                """, (
                    username,
                    password,
                    duration
                ))

                con.commit()
                con.close()

                context.user_data.pop("admin_action", None)

                await update.message.reply_text(
                    f"""
✅ Credential Added

👤 Username: {username}
🔑 Password: {password}
⏳ Duration: {duration} Day
"""
                )

                return

            # Add file
            if admin_action.startswith("file:"):

                file_key = admin_action.split(":", 1)[1]

                if not update.message.document:

                    await update.message.reply_text(
                        "❌ একটি document/file পাঠান।"
                    )
                    return

                document = update.message.document

                con = db()
                cur = con.cursor()

                cur.execute("""
                INSERT OR REPLACE INTO files
                (file_key, telegram_file_id, file_name, updated_at)
                VALUES (?,?,?,?)
                """, (
                    file_key,
                    document.file_id,
                    document.file_name or "file",
                    now_str()
                ))

                con.commit()
                con.close()

                context.user_data.pop("admin_action", None)

                await update.message.reply_text(
                    f"✅ {file_key.upper()} FILE SAVED."
                )

                return

        # -------------------------------------------------
        # BALANCE AMOUNT
        # -------------------------------------------------

        if context.user_data.get("admin_add_balance"):

            try:
                amount = float(text)

                if amount <= 0:
                    raise ValueError

            except:

                await update.message.reply_text(
                    "❌ সঠিক amount দিন।"
                )
                return

            context.user_data["admin_add_balance"] = None
            context.user_data["balance_target"] = None

    # -----------------------------------------------------
    # USER TRANSACTION
    # -----------------------------------------------------

    if context.user_data.get("waiting_tx"):

        context.user_data["waiting_tx"] = False

        product_key = context.user_data.get("selected_product")
        method = context.user_data.get("payment_method")

        if not product_key or not method:
            await update.message.reply_text(
                "❌ Payment session expired। আবার product select করুন।",
                reply_markup=main_menu()
            )
            return

        product = PRODUCTS[product_key]

        con = db()
        cur = con.cursor()

        cur.execute("""
        INSERT INTO orders
        (user_id,product_key,product_name,amount,payment_method,
         transaction_id,status,created_at)
        VALUES (?,?,?,?,?,?,?,?)
        """, (
            user.id,
            product_key,
            product["name"],
            product["price"],
            method,
            text,
            "pending",
            now_str()
        ))

        order_id = cur.lastrowid

        con.commit()
        con.close()

        await update.message.reply_text(
            f"""
✅ PAYMENT SUBMITTED

🧾 Order ID: #{order_id}

📦 {product['name']}

💰 {product['price']} Tk

💳 Payment: {method}

⏳ Status: PENDING

Admin payment verify করার পর
আপনার product automatically পাঠানো হবে।
""",
            reply_markup=main_menu()
        )

        # Admin notification

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"""
🔔 NEW PAYMENT

🧾 Order ID: #{order_id}

👤 User: {user.full_name}
🆔 ID: {user.id}

📦 Product:
{product['name']}

💰 Amount:
{product['price']} Tk

💳 Method:
{method}

🧾 Transaction:
{text}

⏰ Time:
{now_str()}
""",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ ACCEPT",
                        callback_data=f"accept_order:{order_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ REJECT",
                        callback_data=f"reject_order:{order_id}"
                    )
                ]
            ])
        )

        return


# =========================================================
# PROFILE
# =========================================================

async def profile(update, context):

    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    if not user:
        ensure_user(query.from_user)
        user = get_user(query.from_user.id)

    user_id = user[0]
    name = user[1]
    balance = user[3]

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id=? AND status='accepted'",
        (user_id,)
    )
    orders = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE referral_by=?",
        (user_id,)
    )
    referrals = cur.fetchone()[0]

    con.close()

    text = f"""
👤 — YOUR PROFILE —

🆔 User ID:
{user_id}

👤 Name:
{name}

━━━━━━━━━━━━━━━━

💰 BALANCE

💵 Current:
{balance:.2f} Tk

━━━━━━━━━━━━━━━━

📊 STATISTICS

📦 Total Orders: {orders}
🎁 Total Referrals: {referrals}

━━━━━━━━━━━━━━━━

🔗 YOUR REFERRAL LINK

https://t.me/{context.bot.username}?start=ref_{user_id}
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "💰 Add Balance",
                callback_data="add_balance"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Transactions",
                callback_data="transactions"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADD BALANCE
# =========================================================

async def add_balance_menu(update, context):

    query = update.callback_query
    await query.answer()

    context.user_data["waiting_balance_amount"] = True

    await query.message.reply_text(
        """
💰 ADD BALANCE

আপনি কত টাকা Add Balance করতে চান?

উদাহরণ:
300
500
1000
"""
    )


async def handle_balance_amount(update, context):

    if not context.user_data.get("waiting_balance_amount"):
        return False

    text = update.message.text.strip()

    try:
        amount = float(text)

        if amount <= 0:
            raise ValueError

    except:

        await update.message.reply_text(
            "❌ সঠিক amount দিন।"
        )
        return True

    context.user_data["waiting_balance_amount"] = False
    context.user_data["balance_amount"] = amount

    await update.message.reply_text(
        f"""
💰 ADD BALANCE

Amount: {amount:.2f} Tk

🇧🇩 Select Payment Method
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🇧🇩 bKash",
                    callback_data="balancepay:bkash"
                )
            ],
            [
                InlineKeyboardButton(
                    "🟢 Nagad",
                    callback_data="balancepay:nagad"
                )
            ]
        ])
    )

    return True


# =========================================================
# BALANCE PAYMENT
# =========================================================

async def balance_payment(update, context):

    query = update.callback_query
    await query.answer()

    method = query.data.split(":")[1]

    amount = context.user_data.get("balance_amount")

    if not amount:
        await query.message.reply_text(
            "❌ Session expired। আবার Add Balance করুন।"
        )
        return

    if method == "bkash":
        number = BKASH
        method_name = "bKash"
    else:
        number = NAGAD
        method_name = "Nagad"

    context.user_data["balance_payment_method"] = method

    await query.message.reply_text(
        f"""
💰 ADD BALANCE

💵 Amount: {amount:.2f} Tk

💳 Payment: {method_name}

📱 Send Money To:
`{number}`

টাকা পাঠানোর পর
Transaction ID পাঠান।
""",
        parse_mode=ParseMode.MARKDOWN
    )

    context.user_data["waiting_balance_tx"] = True


# =========================================================
# BALANCE TRANSACTION
# =========================================================

async def balance_transaction(update, context):

    if not context.user_data.get("waiting_balance_tx"):
        return False

    context.user_data["waiting_balance_tx"] = False

    user = update.effective_user

    amount = context.user_data.get("balance_amount")
    method = context.user_data.get("balance_payment_method")

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO transactions
    (user_id,amount,payment_method,transaction_id,status,created_at)
    VALUES (?,?,?,?,?,?)
    """, (
        user.id,
        amount,
        method,
        update.message.text.strip(),
        "pending",
        now_str()
    ))

    tx_id = cur.lastrowid

    con.commit()
    con.close()

    await update.message.reply_text(
        f"""
✅ BALANCE REQUEST SUBMITTED

🧾 Request ID: #{tx_id}
💰 Amount: {amount:.2f} Tk
💳 Method: {method}

⏳ Admin verification pending.
"""
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"""
💰 NEW BALANCE REQUEST

🧾 Request: #{tx_id}

👤 User:
{user.full_name}

🆔 ID:
{user.id}

💰 Amount:
{amount:.2f} Tk

💳 Method:
{method}

🧾 Transaction:
{update.message.text.strip()}
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ ACCEPT",
                    callback_data=f"accept_balance:{tx_id}"
                ),
                InlineKeyboardButton(
                    "❌ REJECT",
                    callback_data=f"reject_balance:{tx_id}"
                )
            ]
        ])
    )

    return True


# =========================================================
# ACCEPT / REJECT ORDER
# =========================================================

async def order_action(update, context):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    action, order_id = query.data.split(":")
    order_id = int(order_id)

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT user_id,product_key,amount,status
    FROM orders
    WHERE id=?
    """, (order_id,))

    row = cur.fetchone()

    if not row:
        con.close()
        return

    user_id, product_key, amount, status = row

    if status != "pending":
        con.close()

        await query.edit_message_text(
            "⚠️ This order has already been processed."
        )
        return

    if action == "reject_order":

        cur.execute("""
        UPDATE orders
        SET status='rejected'
        WHERE id=?
        """, (order_id,))

        con.commit()
        con.close()

        await query.edit_message_text(
            f"❌ Order #{order_id} rejected."
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
❌ ORDER REJECTED

🧾 Order: #{order_id}

Payment verification failed.

📩 Support:
{SUPPORT}
"""
        )

        return

    # ACCEPT

    product = PRODUCTS.get(product_key)

    if not product:
        con.close()
        return

    # Credential product
    if product["type"] == "credential":

        cur.execute("""
        SELECT id,username,password,duration
        FROM credentials
        WHERE sold=0 AND duration=?
        ORDER BY id ASC
        LIMIT 1
        """, (product["duration"],))

        credential = cur.fetchone()

        if not credential:

            con.close()

            await query.message.reply_text(
                "❌ No available credential for this duration."
            )
            return

        credential_id, username, password, duration = credential

        expires = now() + timedelta(days=duration)

        cur.execute("""
        UPDATE credentials
        SET sold=1,
            sold_to=?,
            sold_at=?,
            expires_at=?
        WHERE id=?
        """, (
            user_id,
            now_str(),
            expires.strftime("%Y-%m-%d %H:%M:%S"),
            credential_id
        ))

        cur.execute("""
        UPDATE orders
        SET status='accepted',
            delivered_at=?
        WHERE id=?
        """, (
            now_str(),
            order_id
        ))

        con.commit()
        con.close()

        await query.edit_message_text(
            f"✅ Order #{order_id} accepted and delivered."
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
🎉 ORDER SUCCESSFUL

📦 {product['name']}

👤 Username:
`{username}`

🔑 Password:
`{password}`

⏳ Duration:
{duration} Day

📅 Expires:
{expires.strftime("%Y-%m-%d %H:%M:%S")}

⚠️ Login details কাউকে share করবেন না।

📩 Support:
{SUPPORT}
""",
            parse_mode=ParseMode.MARKDOWN
        )

        await referral_check(
            user_id,
            amount,
            context
        )

        return

    # File product

    file_key = product["file_key"]

    cur.execute(
        "SELECT telegram_file_id,file_name FROM files WHERE file_key=?",
        (file_key,)
    )

    file_row = cur.fetchone()

    if not file_row:

        con.close()

        await query.message.reply_text(
            f"❌ {file_key.upper()} file এখনো Admin upload করেননি."
        )
        return

    file_id, file_name = file_row

    cur.execute("""
    UPDATE orders
    SET status='accepted',
        delivered_at=?
    WHERE id=?
    """, (
        now_str(),
        order_id
    ))

    con.commit()
    con.close()

    await query.edit_message_text(
        f"✅ Order #{order_id} accepted and delivered."
    )

    await context.bot.send_document(
        chat_id=user_id,
        document=file_id,
        caption=f"""
🎉 ORDER SUCCESSFUL

📦 {product['name']}

📁 File: {file_name}

📩 Support:
{SUPPORT}
"""
    )

    await referral_check(
        user_id,
        amount,
        context
    )


# =========================================================
# REFERRAL
# =========================================================

async def referral_check(user_id, amount, context):

    if amount < 300:
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT referral_by, referral_rewarded
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cur.fetchone()

    if not row:
        con.close()
        return

    referrer, rewarded = row

    if not referrer or rewarded:
        con.close()
        return

    cur.execute("""
    UPDATE users
    SET balance=balance+50,
        referral_rewarded=1
    WHERE user_id=?
    """, (referrer,))

    cur.execute("""
    UPDATE users
    SET referral_rewarded=1
    WHERE user_id=?
    """, (user_id,))

    con.commit()
    con.close()

    try:
        await context.bot.send_message(
            chat_id=referrer,
            text="""
🎉 REFERRAL REWARD

আপনার referral থেকে একজন user
300 Tk qualifying purchase/deposit করেছে।

💰 আপনার reward:
50 Tk

✅ Referral reward একবারই দেওয়া হয়েছে।
"""
        )
    except:
        pass


async def referral(update, context):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE referral_by=?",
        (user_id,)
    )
    referrals = cur.fetchone()[0]

    con.close()

    text = f"""
🎁 — REFERRAL PROGRAM —

✅ Status: ACTIVE

💰 Earn:
50 Tk

📊 YOUR STATS:

👥 Total Referrals: {referrals}

━━━━━━━━━━━━━━━━

🔗 Your Referral Link:

{link}

━━━━━━━━━━━━━━━━

📱 How it works:

1. Share your link
2. Friend joins using your link
3. Friend adds/purchases 300 Tk or more
4. You get 50 Tk

🎁 Reward is given only once per referred user.
"""

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💰 View Balance",
                    callback_data="profile"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back to Shop",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# LUCKY SPIN
# =========================================================

async def lucky_spin(update, context):

    query = update.callback_query
    await query.answer()

    today = datetime.now().strftime("%Y-%m-%d")

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT result
    FROM spins
    WHERE user_id=? AND spin_date=?
    """, (
        query.from_user.id,
        today
    ))

    already = cur.fetchone()

    con.close()

    if already:

        await query.edit_message_text(
            f"""
🎰 — LUCKY SPIN —

⏰ Already spun today!

🎁 Today's result:
{already[0]} Tk

🕐 Come back tomorrow for another spin!
""",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Back to Shop",
                        callback_data="home"
                    )
                ]
            ])
        )

        return

    await query.edit_message_text(
        """
🎰 — LUCKY SPIN —

🎡 Spinning...

🎁 Checking your reward...
"""
    )

    await asyncio.sleep(3)

    # 0 = no prize
    result = random.randint(0, 15)

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO spins(user_id,spin_date,result)
    VALUES(?,?,?)
    """, (
        query.from_user.id,
        today,
        result
    ))

    con.commit()
    con.close()

    if result == 0:

        result_text = """
😅 No Prize This Time!

Don't worry!
Try again tomorrow.
"""

    else:

        add_balance(query.from_user.id, result)

        result_text = f"""
🎉 CONGRATULATIONS!

💰 You won:
{result} Tk

💵 Added to your balance.
"""

    await query.edit_message_text(
        f"""
🎰 — SPIN RESULT —

━━━━━━━━━━━━━━━━

{result_text}

━━━━━━━━━━━━━━━━

🕐 Next spin:
Tomorrow
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💰 View Balance",
                    callback_data="profile"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back to Shop",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# ORDERS
# =========================================================

async def orders(update, context):

    query = update.callback_query
    await query.answer()

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT id,product_name,amount,status,created_at
    FROM orders
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 10
    """, (query.from_user.id,))

    rows = cur.fetchall()

    con.close()

    if not rows:

        text = """
📦 — MY ORDERS —

No orders yet.
"""

    else:

        text = "📦 — MY ORDERS —\n\n"

        for row in rows:

            text += f"""
🧾 #{row[0]}
📦 {row[1]}
💰 {row[2]} Tk
📌 {row[3].upper()}
⏰ {row[4]}

"""

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# DOWNLOAD FILES
# =========================================================

async def downloads(update, context):

    query = update.callback_query
    await query.answer()

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT DISTINCT product_key
    FROM orders
    WHERE user_id=? AND status='accepted'
    """, (query.from_user.id,))

    rows = cur.fetchall()

    con.close()

    keyboard = []

    for row in rows:

        key = row[0]

        product = PRODUCTS.get(key)

        if product and product["type"] == "file":

            keyboard.append([
                InlineKeyboardButton(
                    f"📁 {product['name']}",
                    callback_data=f"download:{key}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Back",
            callback_data="home"
        )
    ])

    await query.edit_message_text(
        """
📁 — DOWNLOAD FILES —

আপনার purchased files:
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def download_file(update, context):

    query = update.callback_query
    await query.answer()

    key = query.data.split(":", 1)[1]

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT 1
    FROM orders
    WHERE user_id=? AND product_key=? AND status='accepted'
    LIMIT 1
    """, (
        query.from_user.id,
        key
    ))

    purchased = cur.fetchone()

    cur.execute(
        "SELECT telegram_file_id,file_name FROM files WHERE file_key=?",
        (PRODUCTS[key]["file_key"],)
    )

    file_row = cur.fetchone()

    con.close()

    if not purchased:

        await query.message.reply_text(
            "❌ এই file আপনার purchased product নয়।"
        )
        return

    if not file_row:

        await query.message.reply_text(
            "❌ File unavailable."
        )
        return

    await context.bot.send_document(
        chat_id=query.from_user.id,
        document=file_row[0],
        caption=f"📁 {file_row[1]}"
    )


# =========================================================
# TRANSACTIONS
# =========================================================

async def transactions(update, context):

    query = update.callback_query
    await query.answer()

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT amount,payment_method,transaction_id,status,created_at
    FROM transactions
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 10
    """, (query.from_user.id,))

    rows = cur.fetchall()

    con.close()

    if not rows:

        text = "📊 No balance transactions yet."

    else:

        text = "📊 — TRANSACTIONS —\n\n"

        for r in rows:

            text += f"""
💰 Amount: {r[0]} Tk
💳 Method: {r[1]}
🧾 TX: {r[2]}
📌 {r[3].upper()}
⏰ {r[4]}

"""

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="profile"
                )
            ]
        ])
    )


# =========================================================
# ACCEPT / REJECT BALANCE
# =========================================================

async def balance_action(update, context):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    action, txid = query.data.split(":")
    txid = int(txid)

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT user_id,amount,status
    FROM transactions
    WHERE id=?
    """, (txid,))

    row = cur.fetchone()

    if not row:
        con.close()
        return

    user_id, amount, status = row

    if status != "pending":

        con.close()

        await query.edit_message_text(
            "⚠️ Already processed."
        )
        return

    if action == "reject_balance":

        cur.execute("""
        UPDATE transactions
        SET status='rejected'
        WHERE id=?
        """, (txid,))

        con.commit()
        con.close()

        await query.edit_message_text(
            f"❌ Balance request #{txid} rejected."
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
❌ BALANCE REQUEST REJECTED

💰 Amount: {amount} Tk

📩 Support:
{SUPPORT}
"""
        )

        return

    # Accept

    cur.execute("""
    UPDATE transactions
    SET status='accepted'
    WHERE id=?
    """, (txid,))

    cur.execute("""
    UPDATE users
    SET balance=balance+?
    WHERE user_id=?
    """, (
        amount,
        user_id
    ))

    con.commit()
    con.close()

    await query.edit_message_text(
        f"✅ Balance request #{txid} accepted."
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=f"""
🎉 BALANCE ADDED

💰 Added:
{amount:.2f} Tk

💵 Current Balance:
{get_balance(user_id):.2f} Tk
"""
    )

    # Referral reward on balance
    await referral_check(
        user_id,
        amount,
        context
    )


# =========================================================
# SUPPORT
# =========================================================

async def support(update, context):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        f"""
🆘 — SUPPORT —

যেকোনো সমস্যা হলে যোগাযোগ করুন:

👤 Support:
{SUPPORT}

⏰ Please wait for Admin response.
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# TUTORIALS
# =========================================================

async def tutorials(update, context):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        """
📺 — VIDEO TUTORIALS —

🎬 Learn How To Use Our Products

├ 📱 Step-by-step guides
├ 🎮 Game setup tutorials
├ ⚙️ Installation help
└ 💡 Tips & tricks

━━━━━━━━━━━━━━━━

📌 Tutorial videos can be added
to the bot later.
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back to Menu",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin only."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🔑 ADD SABBIR MOD USER/PASS",
                callback_data="admin:add_credential"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD GREEN FILE",
                callback_data="admin:file:green"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD PEST FILE",
                callback_data="admin:file:pest"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD YELLOW FILE",
                callback_data="admin:file:yellow"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD BLUE FILE",
                callback_data="admin:file:blue"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD PINK FILE",
                callback_data="admin:file:pink"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD BR CS FILE",
                callback_data="admin:file:br_cs"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 ADMIN STATS",
                callback_data="admin:stats"
            )
        ],
    ]

    await update.message.reply_text(
        """
👑 — ADMIN PANEL —

Welcome Admin.

নিচের options থেকে কাজ নির্বাচন করুন:
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADMIN CALLBACK
# =========================================================

async def admin_callback(update, context):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    data = query.data

    if data == "admin:add_credential":

        context.user_data["admin_action"] = "add_credential"

        await query.message.reply_text(
            """
🔑 ADD SABBIR MOD PRO ACCOUNT

এই format-এ পাঠান:

username | password | duration

Example:

SABBIR123 | pass123 | 7

Duration:
7
15
30
"""
        )

    elif data.startswith("admin:file:"):

        file_key = data.split(":")[2]

        context.user_data["admin_action"] = f"file:{file_key}"

        await query.message.reply_text(
            f"""
📁 ADD FILE

Product:
{file_key.upper()}

এখন Telegram document হিসেবে
file পাঠান।
"""
        )

    elif data == "admin:stats":

        con = db()
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM credentials WHERE sold=0"
        )
        available_credentials = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM orders WHERE status='pending'"
        )
        pending_orders = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM transactions WHERE status='pending'"
        )
        pending_balance = cur.fetchone()[0]

        con.close()

        await query.message.reply_text(
            f"""
📊 — ADMIN STATS —

👥 Users: {users}

🔑 Available Credentials:
{available_credentials}

🧾 Pending Orders:
{pending_orders}

💰 Pending Balance:
{pending_balance}
"""
        )


# =========================================================
# HOME
# =========================================================

async def home(update, context):

    query = update.callback_query
    await query.answer()

    text = f"""
🏪 — {SHOP_NAME} —

👋 Welcome back, {query.from_user.first_name}!

⭐ — SHOP FEATURES — ⭐

├ 🔑 Premium Game Keys
├ ⚡ Instant Delivery
├ 🔒 Secure Payment
├ 💰 Best Prices
├ 🎁 Referral Rewards
└ 🏆 Professional Support

🚀 Click Shop Now to Start!
"""

    await query.edit_message_text(
        text,
        reply_markup=main_menu()
    )


# =========================================================
# ROUTER FOR TEXT
# =========================================================

async def universal_text(update, context):

    if await handle_balance_amount(update, context):
        return

    if await balance_transaction(update, context):
        return

    await text_handler(update, context)


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable missing."
        )

    if ADMIN_ID == 0:
        raise RuntimeError(
            "ADMIN_ID environment variable missing."
        )

    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("admin", admin)
    )

    # Main callbacks
    app.add_handler(
        CallbackQueryHandler(shop, pattern="^shop$")
    )

    app.add_handler(
        CallbackQueryHandler(home, pattern="^home$")
    )

    app.add_handler(
        CallbackQueryHandler(profile, pattern="^profile$")
    )

    app.add_handler(
        CallbackQueryHandler(orders, pattern="^orders$")
    )

    app.add_handler(
        CallbackQueryHandler(referral, pattern="^referral$")
    )

    app.add_handler(
        CallbackQueryHandler(lucky_spin, pattern="^spin$")
    )

    app.add_handler(
        CallbackQueryHandler(downloads, pattern="^downloads$")
    )

    app.add_handler(
        CallbackQueryHandler(transactions, pattern="^transactions$")
    )

    app.add_handler(
        CallbackQueryHandler(tutorials, pattern="^tutorials$")
    )

    app.add_handler(
        CallbackQueryHandler(support, pattern="^support$")
    )

    app.add_handler(
        CallbackQueryHandler(
            add_balance_menu,
            pattern="^add_balance$"
        )
    )

    # Product
    app.add_handler(
        CallbackQueryHandler(
            product_select,
            pattern="^product:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            payment_method,
            pattern="^paymethod:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            send_tx,
            pattern="^send_tx$"
        )
    )

    # Balance
    app.add_handler(
        CallbackQueryHandler(
            balance_payment,
            pattern="^balancepay:"
        )
    )

    # Download
    app.add_handler(
        CallbackQueryHandler(
            download_file,
            pattern="^download:"
        )
    )

    # Orders
    app.add_handler(
        CallbackQueryHandler(
            order_action,
            pattern="^(accept_order|reject_order):"
        )
    )

    # Balance actions
    app.add_handler(
        CallbackQueryHandler(
            balance_action,
            pattern="^(accept_balance|reject_balance):"
        )
    )

    # Admin
    app.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern="^admin:"
        )
    )

    # Documents for admin
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            universal_text
        )
    )

    # Text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            universal_text
        )
    )

    print("SABBIR MODZ SHOP BOT STARTED")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
