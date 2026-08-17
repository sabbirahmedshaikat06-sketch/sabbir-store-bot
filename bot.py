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

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8752830051"))

SHOP_NAME = "SABBIR MODS SHOP"
SUPPORT = "@sabbirahmed187"

BKASH = "01755196906"
NAGAD = "01706965471"

DB_FILE = "shop.db"


# =========================================================
# PRODUCTS
# =========================================================

PRODUCTS = {
    "sabbir_pro_7": {
        "name": "SABBIR MODE PRO APK - 7 DAY",
        "price": 40,
        "type": "credential",
        "duration": 7,
    },
    "sabbir_pro_15": {
        "name": "SABBIR MODE PRO APK - 15 DAY",
        "price": 80,
        "type": "credential",
        "duration": 15,
    },
    "sabbir_pro_30": {
        "name": "SABBIR MODE PRO APK - 30 DAY",
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
        verified INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    # Compatibility with older database files
    try:
        cur.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

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
        (user_id, name, username, balance,
         referral_by, referral_rewarded,
         verified, created_at)
        VALUES (?, ?, ?, 0, ?, 0, 0, ?)
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


def is_verified(user_id):
    con = db()
    cur = con.cursor()
    cur.execute(
        "SELECT verified FROM users WHERE user_id=?",
        (user_id,)
    )
    row = cur.fetchone()
    con.close()
    return bool(row and row[0] == 1)


def set_verified(user_id):
    con = db()
    cur = con.cursor()
    cur.execute(
        "UPDATE users SET verified=1 WHERE user_id=?",
        (user_id,)
    )
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


def is_admin(user_id):
    return user_id == ADMIN_ID


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🛍️ SHOP NOW", callback_data="shop")
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
# VERIFY
# =========================================================

def verify_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ VERIFY ACCOUNT",
                callback_data="verify_account"
            )
        ]
    ])


async def verify_account(update, context):
    query = update.callback_query
    await query.answer()

    set_verified(query.from_user.id)

    await query.edit_message_text(
        f"""
✅ ACCOUNT VERIFIED

Welcome to {SHOP_NAME}!

আপনার account verification complete হয়েছে।

🛍️ এখন আপনি Shop ব্যবহার করতে পারবেন।
""",
        reply_markup=main_menu()
    )


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
            except ValueError:
                pass

    ensure_user(user, referral_by)

    if not is_verified(user.id):
        await update.message.reply_text(
            f"""
🏪 — {SHOP_NAME} —

👋 Welcome, {user.first_name}!

🔐 ACCOUNT VERIFICATION

Bot ব্যবহার করার আগে আপনার account
verify করুন।

নিচের button-এ click করুন:
""",
            reply_markup=verify_menu()
        )
        return

    await update.message.reply_text(
        f"""
🏪 — {SHOP_NAME} —

👋 Welcome back, {user.first_name}!

⭐ SHOP FEATURES ⭐

├ 🔑 Premium Products
├ ⚡ Fast Delivery
├ 💳 Easy Payment
├ 💰 Best Prices
├ 🎁 Referral Rewards
└ 🏆 Support

🚀 নিচের SHOP NOW button চাপুন।
""",
        reply_markup=main_menu()
    )


# =========================================================
# SHOP
# =========================================================

async def shop(update, context):
    query = update.callback_query
    await query.answer()

    if not is_verified(query.from_user.id):
        await query.message.reply_text("❌ আগে Account Verify করুন।")
        return

    text = f"""
🛍️ — {SHOP_NAME} —

📦 SELECT PRODUCT

নিচে যে product নিতে চান
সেটাতে click করুন।
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 SABBIR MODE PRO APK",
                callback_data="sabbir_pro_menu"
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 BR CS + TOURNAMENT LOCATION",
                callback_data="product:br_cs"
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 PEST TOURNAMENT LOCATION 🩵",
                callback_data="product:pest"
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 PINK TOURNAMENT LOCATION 💜",
                callback_data="product:pink"
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 YELLOW TOURNAMENT LOCATION 💛",
                callback_data="product:yellow"
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 BLUE TOURNAMENT LOCATION 💙",
                callback_data="product:blue"
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 GREEN TOURNAMENT LOCATION 💚",
                callback_data="product:green"
            )
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="home")
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# SABBIR MODE PRO SUB MENU
# =========================================================

async def sabbir_pro_menu(update, context):
    query = update.callback_query
    await query.answer()

    con = db()
    cur = con.cursor()
    stock = {}

    for duration in (7, 15, 30):
        cur.execute("""
        SELECT COUNT(*)
        FROM credentials
        WHERE sold=0 AND duration=?
        """, (duration,))
        stock[duration] = cur.fetchone()[0]

    con.close()

    def stock_text(duration):
        if stock[duration] > 0:
            return f"✅ {stock[duration]}"
        return "❌ 0"

    text = """
🔑 — SABBIR MODE PRO APK —

আপনার পছন্দের মেয়াদ select করুন:

━━━━━━━━━━━━━━━━
💰 PRICE LIST
━━━━━━━━━━━━━━━━

🕐 7 DAY  →  ৳40
🕐 15 DAY →  ৳80
🕐 30 DAY →  ৳120

━━━━━━━━━━━━━━━━
📦 STOCK
━━━━━━━━━━━━━━━━

নিচের button-এ click করুন:
"""

    keyboard = [
        [
            InlineKeyboardButton(
                f"🛒 7 DAY — ৳40 | Stock {stock_text(7)}",
                callback_data="product:sabbir_pro_7"
            )
        ],
        [
            InlineKeyboardButton(
                f"🛒 15 DAY — ৳80 | Stock {stock_text(15)}",
                callback_data="product:sabbir_pro_15"
            )
        ],
        [
            InlineKeyboardButton(
                f"🛒 30 DAY — ৳120 | Stock {stock_text(30)}",
                callback_data="product:sabbir_pro_30"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back to Shop",
                callback_data="shop"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# PRODUCT SELECT
# =========================================================

async def product_select(update, context):
    query = update.callback_query
    await query.answer()

    key = query.data.split(":", 1)[1]
    product = PRODUCTS.get(key)

    if not product:
        await query.message.reply_text("❌ Product পাওয়া যায়নি।")
        return

    context.user_data["selected_product"] = key

    stock_text = "⚠️ Check availability"

    con = db()
    cur = con.cursor()

    if product["type"] == "credential":
        cur.execute("""
        SELECT COUNT(*)
        FROM credentials
        WHERE sold=0 AND duration=?
        """, (product["duration"],))
        count = cur.fetchone()[0]

        if count > 0:
            stock_text = f"✅ In Stock ({count})"
        else:
            stock_text = "❌ Out of Stock"

    else:
        cur.execute("""
        SELECT telegram_file_id
        FROM files
        WHERE file_key=?
        """, (product["file_key"],))
        row = cur.fetchone()

        if row:
            stock_text = "✅ In Stock"
        else:
            stock_text = "❌ Out of Stock"

    con.close()

    text = f"""
🏪 {SHOP_NAME}

📦 {product['name']}

━━━━━━━━━━━━━━━━

📊 STOCK & PRICING

📦 Stock:
{stock_text}

💰 Price:
৳{product['price']}

━━━━━━━━━━━━━━━━

📌 Select payment method below.
"""

    back_callback = "sabbir_pro_menu" if product["type"] == "credential" else "shop"

    keyboard = [
        [
            InlineKeyboardButton(
                "🇧🇩 bKash",
                callback_data="paymethod:bkash"
            )
        ],
        [
            InlineKeyboardButton(
                "🟢 Nagad",
                callback_data="paymethod:nagad"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data=back_callback
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

    if not product_key or product_key not in PRODUCTS:
        await query.edit_message_text(
            "❌ Product session expired.",
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

💰 Price:
৳{product['price']}

💳 Method:
{name}

━━━━━━━━━━━━━━━━

📱 Send Money To:

{number}

━━━━━━━━━━━━━━━━

টাকা পাঠানোর পর নিচের button-এ
click করে Transaction ID পাঠান।
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
                "🔙 Back",
                callback_data=f"product:{product_key}"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# SEND PRODUCT TRANSACTION
# =========================================================

async def send_tx(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["waiting_tx"] = True

    await query.message.reply_text(
        """
🧾 TRANSACTION ID

আপনার Transaction ID লিখে পাঠান।

উদাহরণ:

TX123456789
"""
    )


# =========================================================
# ADD BALANCE MENU
# =========================================================

async def add_balance_menu(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("💵 100 Tk", callback_data="bal_amount:100"),
            InlineKeyboardButton("💵 200 Tk", callback_data="bal_amount:200")
        ],
        [
            InlineKeyboardButton("💵 300 Tk", callback_data="bal_amount:300"),
            InlineKeyboardButton("💵 400 Tk", callback_data="bal_amount:400")
        ],
        [
            InlineKeyboardButton("💵 500 Tk", callback_data="bal_amount:500")
        ],
        [
            InlineKeyboardButton("✏️ Custom Amount", callback_data="bal_custom")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="home")
        ]
    ]

    await query.edit_message_text(
        """
💰 — ADD BALANCE —

আপনি কত টাকা Add Balance করতে চান?

👇 একটি amount select করুন:
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def balance_fixed_amount(update, context):
    query = update.callback_query
    await query.answer()

    amount = float(query.data.split(":")[1])
    context.user_data["balance_amount"] = amount

    await show_balance_payment(query, context, amount)


async def custom_balance(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["waiting_balance_amount"] = True

    await query.edit_message_text(
        """
✏️ CUSTOM AMOUNT

আপনি কত টাকা Add Balance করতে চান?

উদাহরণ:

650
1000
1500

শুধু amount লিখে পাঠান।
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="add_balance"
                )
            ]
        ])
    )


async def handle_balance_amount(update, context):
    if not context.user_data.get("waiting_balance_amount"):
        return False

    text = update.message.text.strip()

    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ সঠিক amount লিখুন।")
        return True

    context.user_data["waiting_balance_amount"] = False
    context.user_data["balance_amount"] = amount

    await show_balance_payment_message(update, context, amount)
    return True


async def show_balance_payment(query, context, amount):
    keyboard = [
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
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="add_balance"
            )
        ]
    ]

    await query.edit_message_text(
        f"""
💰 — ADD BALANCE —

💵 Amount:

৳{amount:.2f}

━━━━━━━━━━━━━━━━

💳 Select Payment Method:
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_balance_payment_message(update, context, amount):
    await update.message.reply_text(
        f"""
💰 — ADD BALANCE —

💵 Amount:

৳{amount:.2f}

💳 Select Payment Method:
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
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="add_balance"
                )
            ]
        ])
    )


# =========================================================
# BALANCE PAYMENT
# =========================================================

async def balance_payment(update, context):
    query = update.callback_query
    await query.answer()

    method = query.data.split(":")[1]
    amount = context.user_data.get("balance_amount")

    if not amount:
        await query.edit_message_text(
            "❌ Session expired.",
            reply_markup=main_menu()
        )
        return

    if method == "bkash":
        number = BKASH
        method_name = "bKash"
    else:
        number = NAGAD
        method_name = "Nagad"

    context.user_data["balance_payment_method"] = method
    context.user_data["waiting_balance_tx"] = True

    await query.edit_message_text(
        f"""
💰 — ADD BALANCE —

💵 Amount:
৳{amount:.2f}

💳 Payment:
{method_name}

━━━━━━━━━━━━━━━━

📱 Send Money To:

{number}

━━━━━━━━━━━━━━━━

টাকা পাঠানোর পর আপনার
Transaction ID লিখে পাঠান।
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="add_balance"
                )
            ]
        ])
    )


async def balance_transaction(update, context):
    if not context.user_data.get("waiting_balance_tx"):
        return False

    context.user_data["waiting_balance_tx"] = False

    user = update.effective_user
    amount = context.user_data.get("balance_amount")
    method = context.user_data.get("balance_payment_method")
    tx_text = update.message.text.strip()

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO transactions
    (user_id, amount, payment_method,
     transaction_id, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        amount,
        method,
        tx_text,
        "pending",
        now_str()
    ))

    tx_id = cur.lastrowid
    con.commit()
    con.close()

    await update.message.reply_text(
        f"""
✅ BALANCE REQUEST SUBMITTED

🧾 Request ID:
#{tx_id}

💰 Amount:
৳{amount:.2f}

💳 Method:
{method}

⏳ Admin verification pending.
""",
        reply_markup=main_menu()
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"""
💰 NEW BALANCE REQUEST

🧾 Request:
#{tx_id}

👤 User:
{user.full_name}

🆔 ID:
{user.id}

💰 Amount:
৳{amount:.2f}

💳 Method:
{method}

🧾 Transaction:
{tx_text}
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

    cur.execute("""
    SELECT COUNT(*)
    FROM orders
    WHERE user_id=? AND status='accepted'
    """, (user_id,))
    orders_count = cur.fetchone()[0]

    cur.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE referral_by=?
    """, (user_id,))
    referrals = cur.fetchone()[0]

    con.close()

    bot_username = context.bot.username

    text = f"""
👤 — YOUR PROFILE —

🆔 User ID:
{user_id}

👤 Name:
{name}

━━━━━━━━━━━━━━━━

💰 BALANCE

💵 Current:
৳{balance:.2f}

━━━━━━━━━━━━━━━━

📊 STATISTICS

📦 Total Orders:
{orders_count}

🎁 Referrals:
{referrals}

━━━━━━━━━━━━━━━━

🔗 REFERRAL LINK

https://t.me/{bot_username}?start=ref_{user_id}
"""

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
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
    SELECT id, product_name, amount,
           status, created_at
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
💰 ৳{row[2]}
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
# REFERRAL
# =========================================================

async def referral(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    link = (
        f"https://t.me/"
        f"{context.bot.username}"
        f"?start=ref_{user_id}"
    )

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

💰 Reward:
50 Tk

👥 Total Referrals:
{referrals}

━━━━━━━━━━━━━━━━

🔗 YOUR REFERRAL LINK

{link}

━━━━━━━━━━━━━━━━

Friend আপনার link দিয়ে join করলে
referral হিসেবে save হবে।
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
                    "🔙 Back",
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
    """, (query.from_user.id, today))

    already = cur.fetchone()
    con.close()

    if already:
        await query.edit_message_text(
            f"""
🎰 — LUCKY SPIN —

আজকে already spin করেছেন।

🎁 Result:
{already[0]} Tk

🕐 Tomorrow আবার try করুন।
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
        return

    await query.edit_message_text(
        """
🎰 — LUCKY SPIN —

🎡 Spinning...

⏳ Please wait...
"""
    )

    await asyncio.sleep(2)
    result = random.randint(0, 15)

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO spins
    (user_id, spin_date, result)
    VALUES (?, ?, ?)
    """, (query.from_user.id, today, result))

    con.commit()
    con.close()

    if result == 0:
        result_text = """
😅 No Prize This Time!

Tomorrow আবার চেষ্টা করুন।
"""
    else:
        add_balance(query.from_user.id, result)
        result_text = f"""
🎉 CONGRATULATIONS!

💰 আপনি পেয়েছেন:
৳{result}

✅ Balance-এ add হয়েছে।
"""

    await query.edit_message_text(
        f"""
🎰 — SPIN RESULT —

━━━━━━━━━━━━━━━━

{result_text}

━━━━━━━━━━━━━━━━

🕐 Next Spin:
Tomorrow
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💰 Profile",
                    callback_data="profile"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# DOWNLOADS
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

    if key not in PRODUCTS:
        return

    product = PRODUCTS[key]

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT 1
    FROM orders
    WHERE user_id=?
    AND product_key=?
    AND status='accepted'
    LIMIT 1
    """, (query.from_user.id, key))

    purchased = cur.fetchone()

    cur.execute("""
    SELECT telegram_file_id,file_name
    FROM files
    WHERE file_key=?
    """, (product["file_key"],))

    file_row = cur.fetchone()
    con.close()

    if not purchased:
        await query.message.reply_text(
            "❌ এই product আপনি purchase করেননি।"
        )
        return

    if not file_row:
        await query.message.reply_text(
            "❌ File এখন available নেই।"
        )
        return

    await context.bot.send_document(
        chat_id=query.from_user.id,
        document=file_row[0],
        caption=f"""
📁 {product['name']}

File:
{file_row[1]}
"""
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
    SELECT amount,payment_method,
           transaction_id,status,created_at
    FROM transactions
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 10
    """, (query.from_user.id,))

    rows = cur.fetchall()
    con.close()

    if not rows:
        text = """
📊 — TRANSACTIONS —

No transactions yet.
"""
    else:
        text = "📊 — TRANSACTIONS —\n\n"

        for r in rows:
            text += f"""
💰 Amount: ৳{r[0]}
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
    SELECT user_id,product_key,
           amount,status
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
        await query.edit_message_text("⚠️ Already processed.")
        return

    product = PRODUCTS.get(product_key)

    if not product:
        con.close()
        return

    # REJECT
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

🧾 Order:
#{order_id}

📩 Support:
{SUPPORT}
"""
        )
        return

    # CREDENTIAL
    if product["type"] == "credential":
        cur.execute("""
        SELECT id,username,password,duration
        FROM credentials
        WHERE sold=0
        AND duration=?
        ORDER BY id ASC
        LIMIT 1
        """, (product["duration"],))

        credential = cur.fetchone()

        if not credential:
            con.close()

            await query.message.reply_text(
                "❌ এই duration-এর কোনো stock নেই।"
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
        """, (now_str(), order_id))

        con.commit()
        con.close()

        await query.edit_message_text(
            f"""
✅ Order #{order_id}

ACCEPTED & DELIVERED
"""
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
🎉 ORDER SUCCESSFUL

📦 {product['name']}

👤 Username:
{username}

🔑 Password:
{password}

⏳ Duration:
{duration} Day

📅 Expires:
{expires.strftime("%Y-%m-%d %H:%M:%S")}

📩 Support:
{SUPPORT}
"""
        )
        return

    # FILE
    file_key = product["file_key"]

    cur.execute("""
    SELECT telegram_file_id,file_name
    FROM files
    WHERE file_key=?
    """, (file_key,))

    file_row = cur.fetchone()

    if not file_row:
        con.close()

        await query.message.reply_text(
            "❌ File Admin এখনো upload করেননি।"
        )
        return

    file_id, file_name = file_row

    cur.execute("""
    UPDATE orders
    SET status='accepted',
        delivered_at=?
    WHERE id=?
    """, (now_str(), order_id))

    con.commit()
    con.close()

    await query.edit_message_text(
        f"""
✅ Order #{order_id}

ACCEPTED & DELIVERED
"""
    )

    await context.bot.send_document(
        chat_id=user_id,
        document=file_id,
        caption=f"""
🎉 ORDER SUCCESSFUL

📦 {product['name']}

📁 File:
{file_name}

📩 Support:
{SUPPORT}
"""
    )


# =========================================================
# BALANCE ACCEPT / REJECT
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
        await query.edit_message_text("⚠️ Already processed.")
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
            f"❌ Balance #{txid} rejected."
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
❌ BALANCE REQUEST REJECTED

💰 Amount:
৳{amount}

📩 Support:
{SUPPORT}
"""
        )
        return

    cur.execute("""
    UPDATE transactions
    SET status='accepted'
    WHERE id=?
    """, (txid,))

    cur.execute("""
    UPDATE users
    SET balance=balance+?
    WHERE user_id=?
    """, (amount, user_id))

    con.commit()
    con.close()

    await query.edit_message_text(
        f"✅ Balance #{txid} accepted."
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=f"""
🎉 BALANCE ADDED

💰 Added:
৳{amount:.2f}

💵 Current Balance:
৳{get_balance(user_id):.2f}
"""
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

├ 📱 Setup Guide
├ ⚙️ Installation Help
├ 🎮 Product Guide
└ 💡 Tips & Tricks

━━━━━━━━━━━━━━━━

Tutorial videos can be added later.
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
# ADMIN PANEL
# =========================================================

async def admin(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🔑 ADD USER/PASS - 7 DAY",
                callback_data="admin:add_credential:7"
            )
        ],
        [
            InlineKeyboardButton(
                "🔑 ADD USER/PASS - 15 DAY",
                callback_data="admin:add_credential:15"
            )
        ],
        [
            InlineKeyboardButton(
                "🔑 ADD USER/PASS - 30 DAY",
                callback_data="admin:add_credential:30"
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
                "📁 ADD PEST FILE 🩵",
                callback_data="admin:file:pest"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD PINK FILE 💜",
                callback_data="admin:file:pink"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD YELLOW FILE 💛",
                callback_data="admin:file:yellow"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD BLUE FILE 💙",
                callback_data="admin:file:blue"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 ADD GREEN FILE 💚",
                callback_data="admin:file:green"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 ADMIN STATS",
                callback_data="admin:stats"
            )
        ]
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

    if data.startswith("admin:add_credential:"):
        duration = data.split(":")[2]

        context.user_data["admin_action"] = f"add_credential:{duration}"

        await query.message.reply_text(
            f"""
🔑 ADD USER/PASSWORD

Duration:
{duration} Day

এই format-এ পাঠান:

username | password

Example:

SABBIR123 | pass123
"""
        )
        return

    if data.startswith("admin:file:"):
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
        return

    if data == "admin:stats":
        con = db()
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]

        cur.execute("""
        SELECT COUNT(*)
        FROM credentials
        WHERE sold=0
        """)
        credentials = cur.fetchone()[0]

        cur.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status='pending'
        """)
        pending_orders = cur.fetchone()[0]

        cur.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE status='pending'
        """)
        pending_balance = cur.fetchone()[0]

        con.close()

        await query.message.reply_text(
            f"""
📊 — ADMIN STATS —

👥 Users:
{users}

🔑 Available Accounts:
{credentials}

🧾 Pending Orders:
{pending_orders}

💰 Pending Balance:
{pending_balance}
"""
        )


# =========================================================
# ADMIN TEXT / FILE HANDLER
# =========================================================

async def admin_message_handler(update, context):
    if not update.message:
        return

    user = update.effective_user

    if not is_admin(user.id):
        return

    action = context.user_data.get("admin_action")

    if not action:
        return

    # FILE
    if action.startswith("file:"):
        if not update.message.document:
            await update.message.reply_text(
                "❌ Telegram document হিসেবে file পাঠান।"
            )
            return

        file_key = action.split(":", 1)[1]
        document = update.message.document

        con = db()
        cur = con.cursor()

        cur.execute("""
        INSERT OR REPLACE INTO files
        (file_key, telegram_file_id,
         file_name, updated_at)
        VALUES (?, ?, ?, ?)
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
            f"""
✅ FILE SAVED

📁 Product:
{file_key.upper()}

📄 File:
{document.file_name or 'file'}
"""
        )
        return

    # CREDENTIAL
    if action.startswith("add_credential:"):
        if not update.message.text:
            return

        duration = int(action.split(":")[1])

        parts = [
            x.strip()
            for x in update.message.text.split("|")
        ]

        if len(parts) != 2:
            await update.message.reply_text(
                """
❌ Format ভুল।

এইভাবে পাঠান:

username | password

Example:

SABBIR123 | pass123
"""
            )
            return

        username = parts[0]
        password = parts[1]

        con = db()
        cur = con.cursor()

        cur.execute("""
        INSERT INTO credentials
        (username,password,duration)
        VALUES (?, ?, ?)
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
✅ ACCOUNT ADDED

👤 Username:
{username}

🔑 Password:
{password}

⏳ Duration:
{duration} Day
"""
        )


# =========================================================
# HOME
# =========================================================

async def home(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        f"""
🏪 — {SHOP_NAME} —

👋 Welcome back,
{query.from_user.first_name}!

⭐ SHOP FEATURES ⭐

├ 📦 Products
├ 💰 Add Balance
├ 🎁 Referral
├ 🎰 Lucky Spin
└ 🆘 Support

🚀 Shop Now চাপুন।
""",
        reply_markup=main_menu()
    )


# =========================================================
# DOCUMENT ROUTER
# =========================================================

async def document_router(update, context):
    if is_admin(update.effective_user.id):
        await admin_message_handler(update, context)


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

    # COMMANDS
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("admin", admin)
    )

    # VERIFY
    app.add_handler(
        CallbackQueryHandler(
            verify_account,
            pattern="^verify_account$"
        )
    )

    # MAIN MENU
    app.add_handler(
        CallbackQueryHandler(
            home,
            pattern="^home$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            shop,
            pattern="^shop$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            profile,
            pattern="^profile$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            orders,
            pattern="^orders$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            referral,
            pattern="^referral$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            lucky_spin,
            pattern="^spin$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            downloads,
            pattern="^downloads$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            transactions,
            pattern="^transactions$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            tutorials,
            pattern="^tutorials$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            support,
            pattern="^support$"
        )
    )

    # ADD BALANCE
    app.add_handler(
        CallbackQueryHandler(
            add_balance_menu,
            pattern="^add_balance$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            balance_fixed_amount,
            pattern="^bal_amount:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            custom_balance,
            pattern="^bal_custom$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            balance_payment,
            pattern="^balancepay:"
        )
    )

    # PRODUCT
    app.add_handler(
        CallbackQueryHandler(
            sabbir_pro_menu,
            pattern="^sabbir_pro_menu$"
        )
    )

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

    # DOWNLOAD
    app.add_handler(
        CallbackQueryHandler(
            download_file,
            pattern="^download:"
        )
    )

    # ORDER ACTION
    app.add_handler(
        CallbackQueryHandler(
            order_action,
            pattern="^(accept_order|reject_order):"
        )
    )

    # BALANCE ACTION
    app.add_handler(
        CallbackQueryHandler(
            balance_action,
            pattern="^(accept_balance|reject_balance):"
        )
    )

    # ADMIN CALLBACK
    app.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern="^admin:"
        )
    )

    # ADMIN DOCUMENT
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            document_router
        )
    )

    # ADMIN TEXT
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & filters.User(user_id=ADMIN_ID)
            & ~filters.COMMAND,
            admin_message_handler
        )
    )

    # NORMAL TEXT
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("SABBIR MODS SHOP BOT STARTED")

    app.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# NORMAL TEXT HANDLER
# =========================================================

async def text_handler(update, context):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    text = update.message.text.strip()

    ensure_user(user)

    # Custom balance
    if await handle_balance_amount(update, context):
        return

    # Balance transaction
    if await balance_transaction(update, context):
        return

    # Product transaction
    if context.user_data.get("waiting_tx"):
        context.user_data["waiting_tx"] = False

        product_key = context.user_data.get("selected_product")
        method = context.user_data.get("payment_method")

        if not product_key or not method:
            await update.message.reply_text(
                "❌ Payment session expired.",
                reply_markup=main_menu()
            )
            return

        product = PRODUCTS.get(product_key)

        if not product:
            await update.message.reply_text(
                "❌ Product পাওয়া যায়নি.",
                reply_markup=main_menu()
            )
            return

        con = db()
        cur = con.cursor()

        cur.execute("""
        INSERT INTO orders
        (user_id, product_key, product_name,
         amount, payment_method,
         transaction_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

🧾 Order:
#{order_id}

📦 Product:
{product['name']}

💰 Amount:
৳{product['price']}

💳 Payment:
{method}

⏳ Status:
PENDING
""",
            reply_markup=main_menu()
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"""
🔔 NEW PAYMENT

🧾 Order:
#{order_id}

👤 User:
{user.full_name}

🆔 ID:
{user.id}

📦 Product:
{product['name']}

💰 Amount:
৳{product['price']}

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


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
