import os, sqlite3, random, asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

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
        "duration": 7
    },

    "sabbir_pro_15": {
        "name": "SABBIR MODE PRO APK - 15 DAY",
        "price": 80,
        "type": "credential",
        "duration": 15
    },

    "sabbir_pro_30": {
        "name": "SABBIR MODE PRO APK - 30 DAY",
        "price": 120,
        "type": "credential",
        "duration": 30
    },

    "br_cs": {
        "name": "BR CS + TOURNAMENT LOCATION",
        "price": 250,
        "type": "file",
        "file_key": "br_cs"
    },

    "pest": {
        "name": "PEST TOURNAMENT LOCATION 🩵",
        "price": 180,
        "type": "file",
        "file_key": "pest"
    },

    "pink": {
        "name": "PINK TOURNAMENT LOCATION 💜",
        "price": 180,
        "type": "file",
        "file_key": "pink"
    },

    "yellow": {
        "name": "YELLOW TOURNAMENT LOCATION 💛",
        "price": 180,
        "type": "file",
        "file_key": "yellow"
    },

    "blue": {
        "name": "BLUE TOURNAMENT LOCATION 💙",
        "price": 180,
        "type": "file",
        "file_key": "blue"
    },

    "green": {
        "name": "GREEN TOURNAMENT LOCATION 💚",
        "price": 180,
        "type": "file",
        "file_key": "green"
    }
}


# =========================================================
# DATABASE
# =========================================================

def db():
    return sqlite3.connect(DB_FILE)


def now():
    return datetime.now()


def now_str():
    return now().strftime("%Y-%m-%d %H:%M:%S")


def init_db():

    con = db()
    c = con.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
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

    try:
        c.execute(
            "ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    c.execute("""
    CREATE TABLE IF NOT EXISTS credentials(
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS files(
        file_key TEXT PRIMARY KEY,
        telegram_file_id TEXT,
        file_name TEXT,
        updated_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS orders(
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS spins(
        user_id INTEGER,
        spin_date TEXT,
        result INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
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

def get_user(uid):

    con = db()
    c = con.cursor()

    c.execute(
        "SELECT * FROM users WHERE user_id=?",
        (uid,)
    )

    r = c.fetchone()

    con.close()

    return r


def ensure_user(u, referral_by=None):

    con = db()
    c = con.cursor()

    c.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (u.id,)
    )

    if not c.fetchone():

        c.execute("""
        INSERT INTO users(
            user_id,
            name,
            username,
            balance,
            referral_by,
            referral_rewarded,
            verified,
            created_at
        )
        VALUES(?,?,?,0,?,0,0,?)
        """, (
            u.id,
            u.full_name,
            u.username or "",
            referral_by,
            now_str()
        ))

    else:

        c.execute("""
        UPDATE users
        SET name=?, username=?
        WHERE user_id=?
        """, (
            u.full_name,
            u.username or "",
            u.id
        ))

    con.commit()
    con.close()


def is_verified(uid):

    con = db()
    c = con.cursor()

    c.execute(
        "SELECT verified FROM users WHERE user_id=?",
        (uid,)
    )

    r = c.fetchone()

    con.close()

    return bool(r and r[0])


def set_verified(uid):

    con = db()
    c = con.cursor()

    c.execute(
        "UPDATE users SET verified=1 WHERE user_id=?",
        (uid,)
    )

    con.commit()
    con.close()


def add_balance(uid, amount):

    con = db()
    c = con.cursor()

    c.execute(
        "UPDATE users SET balance=balance+? WHERE user_id=?",
        (amount, uid)
    )

    con.commit()
    con.close()


def get_balance(uid):

    con = db()
    c = con.cursor()

    c.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (uid,)
    )

    r = c.fetchone()

    con.close()

    return r[0] if r else 0


def is_admin(uid):
    return uid == ADMIN_ID


# =========================================================
# START WELCOME TEXT
# =========================================================

def welcome_text(first_name):

    return f"""
🏪 — {SHOP_NAME} —

👋 Welcome, {first_name}!

⭐ — STORE HIGHLIGHTS — ⭐

│ 🔑 Premium Game Keys
│ ⚡ Instant Delivery 24/7
│ 🔒 100% Secure Payment
│ 💰 Best Prices Guaranteed
│ 🎁 Referral Rewards
│ 📞 Professional Support

━━━━━━━━━━━━━━━━━━━━

🚀 Tap Shop Now to Start!
"""


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🛍️ SHOP NOW",
                callback_data="shop"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 My Orders",
                callback_data="orders"
            ),

            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 Add Balance",
                callback_data="add_balance"
            ),

            InlineKeyboardButton(
                "🎁 Referral",
                callback_data="referral"
            )
        ],

        [
            InlineKeyboardButton(
                "🎰 Lucky Spin",
                callback_data="spin"
            )
        ],

        [
            InlineKeyboardButton(
                "📁 Download Files",
                callback_data="downloads"
            )
        ],

        [
            InlineKeyboardButton(
                "📺 Tutorials",
                callback_data="tutorials"
            ),

            InlineKeyboardButton(
                "🆘 Support",
                callback_data="support"
            )
        ]
    ])


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

    q = update.callback_query

    await q.answer()

    set_verified(q.from_user.id)

    await q.edit_message_text(
        welcome_text(q.from_user.first_name),
        reply_markup=main_menu()
    )


# =========================================================
# START
# =========================================================

async def start(update, context):

    u = update.effective_user

    ref = None

    if context.args:

        arg = context.args[0]

        if arg.startswith("ref_"):

            try:

                rid = int(
                    arg[4:]
                )

                if rid != u.id:
                    ref = rid

            except ValueError:
                pass

    ensure_user(
        u,
        ref
    )

    if not is_verified(u.id):

        await update.message.reply_text(
            f"""
🏪 — {SHOP_NAME} —

👋 Welcome, {u.first_name}!

🔐 ACCOUNT VERIFICATION

Bot ব্যবহার করার আগে আপনার account
verify করুন।

নিচের button-এ click করুন:
""",
            reply_markup=verify_menu()
        )

        return

    await update.message.reply_text(
        welcome_text(
            u.first_name
        ),
        reply_markup=main_menu()
    )


# =========================================================
# SHOP
# =========================================================

async def shop(update, context):

    q = update.callback_query

    await q.answer()

    if not is_verified(q.from_user.id):

        await q.message.reply_text(
            "❌ আগে Account Verify করুন।"
        )

        return

    kb = [

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
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    ]

    await q.edit_message_text(
        f"""
🛍️ — {SHOP_NAME} —

📦 SELECT PRODUCT

নিচে যে product নিতে চান
সেটাতে click করুন।
""",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# =========================================================
# SABBIR MODE PRO PRICE LIST
# =========================================================

async def sabbir_pro_menu(update, context):

    q = update.callback_query

    await q.answer()

    con = db()
    c = con.cursor()

    stock = {}

    for d in (7, 15, 30):

        c.execute(
            """
            SELECT COUNT(*)
            FROM credentials
            WHERE sold=0
            AND duration=?
            """,
            (d,)
        )

        stock[d] = c.fetchone()[0]

    con.close()

    def sd(d):

        n = stock[d]

        if 0 < n <= 4:

            return f"⚠️ {n} Left", "⚠️"

        if n <= 0:

            return "❌ Out of Stock", "❌"

        return "✅ In Stock", "✅"

    s7, i7 = sd(7)
    s15, i15 = sd(15)
    s30, i30 = sd(30)

    text = f"""
🔑 SABBIR MODE PRO APK

━━━━━━━━━━━━━━━━━━━━
📦 STOCK & PRICING
━━━━━━━━━━━━━━━━━━━━

{i7} 7 Day
├ 📦 Stock: {s7}
└ 💰 Price: ৳40

━━━━━━━━━━━━━━━━━━━━

{i15} 15 Days
├ 📦 Stock: {s15}
└ 💰 Price: ৳80

━━━━━━━━━━━━━━━━━━━━

{i30} 30 Days
├ 📦 Stock: {s30}
└ 💰 Price: ৳120

━━━━━━━━━━━━━━━━━━━━

📩 Support: {SUPPORT}

🎯 Select your plan below:
"""

    kb = [

        [
            InlineKeyboardButton(
                "🛒 Buy 7 Day — ৳40",
                callback_data="product:sabbir_pro_7"
            )
        ],

        [
            InlineKeyboardButton(
                "🛒 Buy 15 Days — ৳80",
                callback_data="product:sabbir_pro_15"
            )
        ],

        [
            InlineKeyboardButton(
                "🛒 Buy 30 Days — ৳120",
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

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb)
    )


# =========================================================
# PRODUCT SELECT
# =========================================================

async def product_select(update, context):

    q = update.callback_query

    await q.answer()

    key = q.data.split(
        ":",
        1
    )[1]

    p = PRODUCTS.get(key)

    if not p:

        await q.message.reply_text(
            "❌ Product পাওয়া যায়নি।"
        )

        return

    con = db()
    c = con.cursor()

    if p["type"] == "credential":

        c.execute(
            """
            SELECT COUNT(*)
            FROM credentials
            WHERE sold=0
            AND duration=?
            """,
            (p["duration"],)
        )

        n = c.fetchone()[0]

        if 0 < n <= 4:

            stock = f"⚠️ {n} Left"

        elif n > 0:

            stock = f"✅ In Stock ({n})"

        else:

            stock = "❌ Out of Stock"

    else:

        c.execute(
            """
            SELECT telegram_file_id
            FROM files
            WHERE file_key=?
            """,
            (p["file_key"],)
        )

        stock = (
            "✅ In Stock"
            if c.fetchone()
            else
            "❌ Out of Stock"
        )

    con.close()

    back = (
        "sabbir_pro_menu"
        if p["type"] == "credential"
        else
        "shop"
    )

    if stock == "❌ Out of Stock":

        await q.edit_message_text(
            f"""
❌ OUT OF STOCK

📦 Product:
{p['name']}

📊 Stock:
❌ Out of Stock

💰 Price:
৳{p['price']}

দুঃখিত, এই product এখন available নেই।
""",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data=back
                    )
                ]
            ])
        )

        return

    context.user_data[
        "selected_product"
    ] = key

    await q.edit_message_text(
        f"""
🏪 {SHOP_NAME}

📦 {p['name']}

━━━━━━━━━━━━━━━━

📊 STOCK & PRICING

📦 Stock:
{stock}

💰 Price:
৳{p['price']}

━━━━━━━━━━━━━━━━

📌 Select payment method below.
""",
        reply_markup=InlineKeyboardMarkup([

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
                    callback_data=back
                )
            ]
        ])
    )


# =========================================================
# PAYMENT METHOD
# =========================================================

async def payment_method(update, context):

    q = update.callback_query

    await q.answer()

    method = q.data.split(":")[1]

    key = context.user_data.get(
        "selected_product"
    )

    if not key or key not in PRODUCTS:

        await q.edit_message_text(
            "❌ Product session expired.",
            reply_markup=main_menu()
        )

        return

    p = PRODUCTS[key]

    con = db()
    c = con.cursor()

    if p["type"] == "credential":

        c.execute(
            """
            SELECT COUNT(*)
            FROM credentials
            WHERE sold=0
            AND duration=?
            """,
            (p["duration"],)
        )

        ok = c.fetchone()[0] > 0

    else:

        c.execute(
            """
            SELECT telegram_file_id
            FROM files
            WHERE file_key=?
            """,
            (p["file_key"],)
        )

        ok = bool(c.fetchone())

    con.close()

    if not ok:

        back = (
            "sabbir_pro_menu"
            if p["type"] == "credential"
            else
            "shop"
        )

        await q.edit_message_text(
            "❌ এই product এখন Out of Stock।",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data=back
                    )
                ]
            ])
        )

        return

    number = (
        BKASH
        if method == "bkash"
        else
        NAGAD
    )

    name = (
        "bKash"
        if method == "bkash"
        else
        "Nagad"
    )

    context.user_data[
        "payment_method"
    ] = method

    await q.edit_message_text(
        f"""
💳 PAYMENT INFORMATION

📦 Product:
{p['name']}

💰 Price:
৳{p['price']}

💳 Method:
{name}

━━━━━━━━━━━━━━━━

📱 Send Money To:

{number}

━━━━━━━━━━━━━━━━

টাকা পাঠানোর পর নিচের button-এ
click করে Transaction ID পাঠান।
""",
        reply_markup=InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🧾 Transaction ID পাঠান",
                    callback_data="send_tx"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data=f"product:{key}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# SEND TRANSACTION
# =========================================================

async def send_tx(update, context):

    q = update.callback_query

    await q.answer()

    context.user_data[
        "waiting_tx"
    ] = True

    await q.message.reply_text(
        """
🧾 TRANSACTION ID

আপনার Transaction ID লিখে পাঠান।

উদাহরণ:

TX123456789
"""
    )


# =========================================================
# ADD BALANCE
# =========================================================

async def add_balance_menu(update, context):

    q = update.callback_query

    await q.answer()

    kb = [

        [
            InlineKeyboardButton(
                "💵 100 Tk",
                callback_data="bal_amount:100"
            ),

            InlineKeyboardButton(
                "💵 200 Tk",
                callback_data="bal_amount:200"
            )
        ],

        [
            InlineKeyboardButton(
                "💵 300 Tk",
                callback_data="bal_amount:300"
            ),

            InlineKeyboardButton(
                "💵 400 Tk",
                callback_data="bal_amount:400"
            )
        ],

        [
            InlineKeyboardButton(
                "💵 500 Tk",
                callback_data="bal_amount:500"
            )
        ],

        [
            InlineKeyboardButton(
                "✏️ Custom Amount",
                callback_data="bal_custom"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    ]

    await q.edit_message_text(
        """
💰 — ADD BALANCE —

আপনি কত টাকা Add Balance করতে চান?

👇 একটি amount select করুন:
""",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def balance_fixed_amount(update, context):

    q = update.callback_query

    await q.answer()

    amount = float(
        q.data.split(":")[1]
    )

    context.user_data[
        "balance_amount"
    ] = amount

    await show_balance_payment(
        q,
        context,
        amount
    )


async def custom_balance(update, context):

    q = update.callback_query

    await q.answer()

    context.user_data[
        "waiting_balance_amount"
    ] = True

    await q.edit_message_text(
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


async def show_balance_payment(
    q,
    context,
    amount
):

    await q.edit_message_text(
        f"""
💰 — ADD BALANCE —

💵 Amount:

৳{amount:.2f}

━━━━━━━━━━━━━━━━

💳 Select Payment Method:
""",
        reply_markup=InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    " bKash",
                    callback_data="balancepay:bkash"
                )
            ],

            [
                InlineKeyboardButton(
                    " Nagad",
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


async def show_balance_payment_message(
    update,
    context,
    amount
):

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
                    " bKash",
                    callback_data="balancepay:bkash"
                )
            ],

            [
                InlineKeyboardButton(
                    " Nagad",
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


async def balance_payment(update, context):

    q = update.callback_query

    await q.answer()

    method = q.data.split(":")[1]

    amount = context.user_data.get(
        "balance_amount"
    )

    if not amount:

        await q.edit_message_text(
            "❌ Session expired.",
            reply_markup=main_menu()
        )

        return

    number = (
        BKASH
        if method == "bkash"
        else
        NAGAD
    )

    name = (
        "bKash"
        if method == "bkash"
        else
        "Nagad"
    )

    context.user_data[
        "balance_payment_method"
    ] = method

    context.user_data[
        "waiting_balance_tx"
    ] = True

    await q.edit_message_text(
        f"""
💰 — ADD BALANCE —

💵 Amount:
৳{amount:.2f}

💳 Payment:
{name}

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


async def handle_balance_amount(update, context):

    if not context.user_data.get(
        "waiting_balance_amount"
    ):
        return False

    try:

        amount = float(
            update.message.text.strip()
        )

        if amount <= 0:
            raise ValueError

    except:

        await update.message.reply_text(
            "❌ সঠিক amount লিখুন।"
        )

        return True

    context.user_data[
        "waiting_balance_amount"
    ] = False

    context.user_data[
        "balance_amount"
    ] = amount

    await show_balance_payment_message(
        update,
        context,
        amount
    )

    return True


async def balance_transaction(update, context):

    if not context.user_data.get(
        "waiting_balance_tx"
    ):
        return False

    context.user_data[
        "waiting_balance_tx"
    ] = False

    u = update.effective_user

    amount = context.user_data.get(
        "balance_amount"
    )

    method = context.user_data.get(
        "balance_payment_method"
    )

    tx = update.message.text.strip()

    con = db()
    c = con.cursor()

    c.execute("""
    INSERT INTO transactions(
        user_id,
        amount,
        payment_method,
        transaction_id,
        status,
        created_at
    )
    VALUES(?,?,?,?,?,?)
    """, (
        u.id,
        amount,
        method,
        tx,
        "pending",
        now_str()
    ))

    tid = c.lastrowid

    con.commit()
    con.close()

    await update.message.reply_text(
        f"""
✅ BALANCE REQUEST SUBMITTED

🧾 Request ID:
#{tid}

💰 Amount:
৳{amount:.2f}

💳 Method:
{method}

⏳ Admin verification pending.
""",
        reply_markup=main_menu()
    )

    await context.bot.send_message(
        ADMIN_ID,
        f"""
💰 NEW BALANCE REQUEST

🧾 Request:
#{tid}

👤 User:
{u.full_name}

🆔 ID:
{u.id}

💰 Amount:
৳{amount:.2f}

💳 Method:
{method}

🧾 Transaction:
{tx}
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ ACCEPT",
                    callback_data=f"accept_balance:{tid}"
                ),

                InlineKeyboardButton(
                    "❌ REJECT",
                    callback_data=f"reject_balance:{tid}"
                )
            ]
        ])
    )

    return True


# =========================================================
# PROFILE
# =========================================================

async def profile(update, context):

    q = update.callback_query

    await q.answer()

    u = get_user(
        q.from_user.id
    )

    if not u:

        ensure_user(
            q.from_user
        )

        u = get_user(
            q.from_user.id
        )

    con = db()
    c = con.cursor()

    c.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE user_id=?
        AND status='accepted'
        """,
        (u[0],)
    )

    orders_count = c.fetchone()[0]

    c.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE referral_by=?
        """,
        (u[0],)
    )

    referrals = c.fetchone()[0]

    con.close()

    await q.edit_message_text(
        f"""
👤 — YOUR PROFILE —

🆔 User ID:
{u[0]}

👤 Name:
{u[1]}

━━━━━━━━━━━━━━━━

💰 BALANCE

💵 Current:
৳{u[3]:.2f}

━━━━━━━━━━━━━━━━

📊 STATISTICS

📦 Total Orders:
{orders_count}

🎁 Referrals:
{referrals}

━━━━━━━━━━━━━━━━

🔗 REFERRAL LINK

https://t.me/{context.bot.username}?start=ref_{u[0]}
""",
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

    q = update.callback_query

    await q.answer()

    con = db()
    c = con.cursor()

    c.execute(
        """
        SELECT
            id,
            product_name,
            amount,
            status,
            created_at
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (q.from_user.id,)
    )

    rows = c.fetchall()

    con.close()

    text = "📦 — MY ORDERS —\n\n"

    if not rows:

        text += "No orders yet."

    else:

        for r in rows:

            text += f"""
🧾 #{r[0]}
📦 {r[1]}
💰 ৳{r[2]}
📌 {r[3].upper()}
⏰ {r[4]}

"""

    await q.edit_message_text(
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

    q = update.callback_query

    await q.answer()

    uid = q.from_user.id

    link = (
        f"https://t.me/"
        f"{context.bot.username}"
        f"?start=ref_{uid}"
    )

    con = db()
    c = con.cursor()

    c.execute(
        "SELECT COUNT(*) FROM users WHERE referral_by=?",
        (uid,)
    )

    n = c.fetchone()[0]

    con.close()

    await q.edit_message_text(
        f"""
🎁 — REFERRAL PROGRAM —

💰 Reward:
50 Tk

👥 Total Referrals:
{n}

━━━━━━━━━━━━━━━━

🔗 YOUR REFERRAL LINK

{link}

━━━━━━━━━━━━━━━━

Friend আপনার link দিয়ে join করলে
referral হিসেবে save হবে।
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

    q = update.callback_query

    await q.answer()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    con = db()
    c = con.cursor()

    c.execute(
        """
        SELECT result
        FROM spins
        WHERE user_id=?
        AND spin_date=?
        """,
        (
            q.from_user.id,
            today
        )
    )

    old = c.fetchone()

    con.close()

    if old:

        await q.edit_message_text(
            f"""
🎰 — LUCKY SPIN —

আজকে already spin করেছেন।

🎁 Result:
{old[0]} Tk

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

    await q.edit_message_text(
        """
🎰 — LUCKY SPIN —

🎡 Spinning...

⏳ Please wait...
"""
    )

    await asyncio.sleep(2)

    result = random.randint(
        0,
        15
    )

    con = db()
    c = con.cursor()

    c.execute(
        """
        INSERT INTO spins(
            user_id,
            spin_date,
            result
        )
        VALUES(?,?,?)
        """,
        (
            q.from_user.id,
            today,
            result
        )
    )

    con.commit()
    con.close()

    if result:

        add_balance(
            q.from_user.id,
            result
        )

        rt = f"""
🎉 CONGRATULATIONS!

💰 আপনি পেয়েছেন:
৳{result}

✅ Balance-এ add হয়েছে.
"""

    else:

        rt = """
😅 No Prize This Time!

Tomorrow আবার চেষ্টা করুন।
"""

    await q.edit_message_text(
        f"""
🎰 — SPIN RESULT —

━━━━━━━━━━━━━━━━

{rt}

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

    q = update.callback_query

    await q.answer()

    con = db()
    c = con.cursor()

    c.execute(
        """
        SELECT DISTINCT product_key
        FROM orders
        WHERE user_id=?
        AND status='accepted'
        """,
        (q.from_user.id,)
    )

    rows = c.fetchall()

    con.close()

    kb = []

    for row in rows:

        key = row[0]

        p = PRODUCTS.get(key)

        if p and p["type"] == "file":

            kb.append([
                InlineKeyboardButton(
                    f"📁 {p['name']}",
                    callback_data=f"download:{key}"
                )
            ])

    kb.append([
        InlineKeyboardButton(
            "🔙 Back",
            callback_data="home"
        )
    ])

    await q.edit_message_text(
        """
📁 — DOWNLOAD FILES —

আপনার purchased files:
""",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def download_file(update, context):

    q = update.callback_query

    await q.answer()

    key = q.data.split(
        ":",
        1
    )[1]

    p = PRODUCTS.get(key)

    if not p:
        return

    con = db()
    c = con.cursor()

    c.execute(
        """
        SELECT 1
        FROM orders
        WHERE user_id=?
        AND product_key=?
        AND status='accepted'
        LIMIT 1
        """,
        (
            q.from_user.id,
            key
        )
    )

    bought = c.fetchone()

    c.execute(
        """
        SELECT telegram_file_id,file_name
        FROM files
        WHERE file_key=?
        """,
        (p["file_key"],)
    )

    f = c.fetchone()

    con.close()

    if not bought:

        await q.message.reply_text(
            "❌ এই product আপনি purchase করেননি।"
        )

        return

    if not f:

        await q.message.reply_text(
            "❌ File এখন available নেই।"
        )

        return

    await context.bot.send_document(
        q.from_user.id,
        f[0],
        caption=f"""
📁 {p['name']}

File:
{f[1]}
"""
    )


# =========================================================
# TRANSACTIONS
# =========================================================

async def transactions(update, context):

    q = update.callback_query

    await q.answer()

    con = db()
    c = con.cursor()

    c.execute(
        """
        SELECT
            amount,
            payment_method,
            transaction_id,
            status,
            created_at
        FROM transactions
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (q.from_user.id,)
    )

    rows = c.fetchall()

    con.close()

    text = "📊 — TRANSACTIONS —\n\n"

    if not rows:

        text += "No transactions yet."

    else:

        for r in rows:

            text += f"""
💰 Amount: ৳{r[0]}
💳 Method: {r[1]}
🧾 TX: {r[2]}
📌 {r[3].upper()}
⏰ {r[4]}

"""

    await q.edit_message_text(
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
# ORDER ACTION
# =========================================================

async def order_action(update, context):

    q = update.callback_query

    await q.answer()

    if not is_admin(q.from_user.id):
        return

    action, oid = q.data.split(":")

    oid = int(oid)

    con = db()
    c = con.cursor()

    c.execute(
        """
        SELECT
            user_id,
            product_key,
            amount,
            status
        FROM orders
        WHERE id=?
        """,
        (oid,)
    )

    row = c.fetchone()

    if not row:

        con.close()
        return

    uid, key, amount, status = row

    if status != "pending":

        con.close()

        await q.edit_message_text(
            "⚠️ Already processed."
        )

        return

    p = PRODUCTS.get(key)

    if not p:

        con.close()
        return

    if action == "reject_order":

        c.execute(
            """
            UPDATE orders
            SET status='rejected'
            WHERE id=?
            """,
            (oid,)
        )

        con.commit()
        con.close()

        await q.edit_message_text(
            f"❌ Order #{oid} rejected."
        )

        await context.bot.send_message(
            uid,
            f"""
❌ ORDER REJECTED

🧾 Order:
#{oid}

📩 Support:
{SUPPORT}
"""
        )

        return

    if p["type"] == "credential":

        c.execute(
            """
            SELECT
                id,
                username,
                password,
                duration
            FROM credentials
            WHERE sold=0
            AND duration=?
            ORDER BY id
            LIMIT 1
            """,
            (p["duration"],)
        )

        cred = c.fetchone()

        if not cred:

            con.close()

            await q.message.reply_text(
                "❌ এই duration-এর কোনো stock নেই।"
            )

            return

        cid = cred[0]
        username = cred[1]
        password = cred[2]
        dur = cred[3]

        exp = now() + timedelta(
            days=dur
        )

        c.execute(
            """
            UPDATE credentials
            SET
                sold=1,
                sold_to=?,
                sold_at=?,
                expires_at=?
            WHERE id=?
            """,
            (
                uid,
                now_str(),
                exp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                cid
            )
        )

        c.execute(
            """
            UPDATE orders
            SET
                status='accepted',
                delivered_at=?
            WHERE id=?
            """,
            (
                now_str(),
                oid
            )
        )

        con.commit()
        con.close()

        await q.edit_message_text(
            f"""
✅ Order #{oid}

ACCEPTED & DELIVERED
"""
        )

        await context.bot.send_message(
            uid,
            f"""
🎉 ORDER SUCCESSFUL

📦 {p['name']}

👤 Username:
{username}

🔑 Password:
{password}

⏳ Duration:
{dur} Day

📅 Expires:
{exp.strftime("%Y-%m-%d %H:%M:%S")}

📩 Support:
{SUPPORT}
"""
        )

        return

    c.execute(
        """
        SELECT
            telegram_file_id,
            file_name
        FROM files
        WHERE file_key=?
        """,
        (p["file_key"],)
    )

    f = c.fetchone()

    if not f:

        con.close()

        await q.message.reply_text(
            "❌ File Admin এখনো upload করেননি।"
        )

        return

    c.execute(
        """
        UPDATE orders
        SET
            status='accepted',
            delivered_at=?
        WHERE id=?
        """,
        (
            now_str(),
            oid
        )
    )

    con.commit()
    con.close()

    await q.edit_message_text(
        f"""
✅ Order #{oid}

ACCEPTED & DELIVERED
"""
    )

    await context.bot.send_document(
        uid,
        f[0],
        caption=f"""
🎉 ORDER SUCCESSFUL

📦 {p['name']}

📁 File:
{f[1]}

📩 Support:
{SUPPORT}
"""
    )


# =========================================================
# BALANCE ACTION
# =========================================================

async def balance_action(update, context):

    q = update.callback_query

    await q.answer()

    if not is_admin(q.from_user.id):
        return

    action, tid = q.data.split(":")

    tid = int(tid)

    con = db()
    c = con.cursor()

    c.execute(
        """
        SELECT
            user_id,
            amount,
            status
        FROM transactions
        WHERE id=?
        """,
        (tid,)
    )

    row = c.fetchone()

    if not row:

        con.close()
        return

    uid, amount, status = row

    if status != "pending":

        con.close()

        await q.edit_message_text(
            "⚠️ Already processed."
        )

        return

    if action == "reject_balance":

        c.execute(
            """
            UPDATE transactions
            SET status='rejected'
            WHERE id=?
            """,
            (tid,)
        )

        con.commit()
        con.close()

        await q.edit_message_text(
            f"❌ Balance #{tid} rejected."
        )

        await context.bot.send_message(
            uid,
            f"""
❌ BALANCE REQUEST REJECTED

💰 Amount:
৳{amount}

📩 Support:
{SUPPORT}
"""
        )

        return

    c.execute(
        """
        UPDATE transactions
        SET status='accepted'
        WHERE id=?
        """,
        (tid,)
    )

    c.execute(
        """
        UPDATE users
        SET balance=balance+?
        WHERE user_id=?
        """,
        (
            amount,
            uid
        )
    )

    con.commit()
    con.close()

    await q.edit_message_text(
        f"✅ Balance #{tid} accepted."
    )

    await context.bot.send_message(
        uid,
        f"""
🎉 BALANCE ADDED

💰 Added:
৳{amount:.2f}

💵 Current Balance:
৳{get_balance(uid):.2f}
"""
    )


# =========================================================
# SUPPORT
# =========================================================

async def support(update, context):

    q = update.callback_query

    await q.answer()

    await q.edit_message_text(
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

    q = update.callback_query

    await q.answer()

    await q.edit_message_text(
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

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Admin only."
        )

        return

    kb = [

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
        reply_markup=InlineKeyboardMarkup(kb)
    )


# =========================================================
# ADMIN CALLBACK
# =========================================================

async def admin_callback(update, context):

    q = update.callback_query

    await q.answer()

    if not is_admin(
        q.from_user.id
    ):
        return

    d = q.data

    if d.startswith(
        "admin:add_credential:"
    ):

        dur = d.split(":")[2]

        context.user_data[
            "admin_action"
        ] = f"add_credential:{dur}"

        await q.message.reply_text(
            f"""
🔑 ADD USER/PASSWORD

Duration:
{dur} Day

এই format-এ পাঠান:

username | password

Example:

SABBIR123 | pass123
"""
        )

        return

    if d.startswith(
        "admin:file:"
    ):

        fk = d.split(":")[2]

        context.user_data[
            "admin_action"
        ] = f"file:{fk}"

        await q.message.reply_text(
            f"""
📁 ADD FILE

Product:
{fk.upper()}

এখন Telegram document হিসেবে
file পাঠান।
"""
        )

        return

    if d == "admin:stats":

        con = db()
        c = con.cursor()

        c.execute(
            "SELECT COUNT(*) FROM users"
        )

        users = c.fetchone()[0]

        c.execute(
            """
            SELECT COUNT(*)
            FROM credentials
            WHERE sold=0
            """
        )

        creds = c.fetchone()[0]

        c.execute(
            """
            SELECT COUNT(*)
            FROM orders
            WHERE status='pending'
            """
        )

        po = c.fetchone()[0]

        c.execute(
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE status='pending'
            """
        )

        pb = c.fetchone()[0]

        con.close()

        await q.message.reply_text(
            f"""
📊 — ADMIN STATS —

👥 Users:
{users}

🔑 Available Accounts:
{creds}

🧾 Pending Orders:
{po}

💰 Pending Balance:
{pb}
"""
        )


# =========================================================
# ADMIN MESSAGE HANDLER
# =========================================================

async def admin_message_handler(
    update,
    context
):

    if not update.message:
        return

    if not is_admin(
        update.effective_user.id
    ):
        return

    action = context.user_data.get(
        "admin_action"
    )

    if not action:
        return

    if action.startswith(
        "file:"
    ):

        if not update.message.document:

            await update.message.reply_text(
                "❌ Telegram document হিসেবে file পাঠান।"
            )

            return

        fk = action.split(
            ":",
            1
        )[1]

        doc = update.message.document

        con = db()
        c = con.cursor()

        c.execute(
            """
            INSERT OR REPLACE INTO files(
                file_key,
                telegram_file_id,
                file_name,
                updated_at
            )
            VALUES(?,?,?,?)
            """,
            (
                fk,
                doc.file_id,
                doc.file_name or "file",
                now_str()
            )
        )

        con.commit()
        con.close()

        context.user_data.pop(
            "admin_action",
            None
        )

        await update.message.reply_text(
            f"""
✅ FILE SAVED

📁 Product:
{fk.upper()}

📄 File:
{doc.file_name or 'file'}
"""
        )

        return

    if action.startswith(
        "add_credential:"
    ):

        parts = [
            x.strip()
            for x in
            (update.message.text or "").split("|")
        ]

        if len(parts) != 2:

            await update.message.reply_text(
                """
❌ Format ভুল।

username | password
"""
            )

            return

        dur = int(
            action.split(":")[1]
        )

        con = db()
        c = con.cursor()

        c.execute(
            """
            INSERT INTO credentials(
                username,
                password,
                duration
            )
            VALUES(?,?,?)
            """,
            (
                parts[0],
                parts[1],
                dur
            )
        )

        con.commit()
        con.close()

        context.user_data.pop(
            "admin_action",
            None
        )

        await update.message.reply_text(
            f"""
✅ ACCOUNT ADDED

👤 Username:
{parts[0]}

🔑 Password:
{parts[1]}

⏳ Duration:
{dur} Day
"""
        )


# =========================================================
# DOCUMENT ROUTER
# =========================================================

async def document_router(
    update,
    context
):

    if is_admin(
        update.effective_user.id
    ):

        await admin_message_handler(
            update,
            context
        )


# =========================================================
# HOME
# =========================================================

async def home(update, context):

    q = update.callback_query

    await q.answer()

    await q.edit_message_text(
        welcome_text(
            q.from_user.first_name
        ),
        reply_markup=main_menu()
    )


# =========================================================
# NORMAL TEXT HANDLER
# =========================================================

async def text_handler(
    update,
    context
):

    if not update.message:
        return

    if not update.message.text:
        return

    u = update.effective_user

    text = update.message.text.strip()

    ensure_user(u)

    if is_admin(u.id):

        if context.user_data.get(
            "admin_action"
        ):

            await admin_message_handler(
                update,
                context
            )

            return

    if await handle_balance_amount(
        update,
        context
    ):

        return

    if await balance_transaction(
        update,
        context
    ):

        return

    if context.user_data.get(
        "waiting_tx"
    ):

        context.user_data[
            "waiting_tx"
        ] = False

        key = context.user_data.get(
            "selected_product"
        )

        method = context.user_data.get(
            "payment_method"
        )

        if not key or not method:

            await update.message.reply_text(
                "❌ Payment session expired.",
                reply_markup=main_menu()
            )

            return

        p = PRODUCTS.get(key)

        if not p:

            await update.message.reply_text(
                "❌ Product পাওয়া যায়নি.",
                reply_markup=main_menu()
            )

            return

        con = db()
        c = con.cursor()

        if p["type"] == "credential":

            c.execute(
                """
                SELECT COUNT(*)
                FROM credentials
                WHERE sold=0
                AND duration=?
                """,
                (p["duration"],)
            )

            ok = c.fetchone()[0] > 0

        else:

            c.execute(
                """
                SELECT telegram_file_id
                FROM files
                WHERE file_key=?
                """,
                (p["file_key"],)
            )

            ok = bool(
                c.fetchone()
            )

        if not ok:

            con.close()

            await update.message.reply_text(
                "❌ দুঃখিত, এই product এখন Out of Stock।",
                reply_markup=main_menu()
            )

            return

        c.execute(
            """
            INSERT INTO orders(
                user_id,
                product_key,
                product_name,
                amount,
                payment_method,
                transaction_id,
                status,
                created_at
            )
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                u.id,
                key,
                p["name"],
                p["price"],
                method,
                text,
                "pending",
                now_str()
            )
        )

        oid = c.lastrowid

        con.commit()
        con.close()

        await update.message.reply_text(
            f"""
✅ PAYMENT SUBMITTED

🧾 Order:
#{oid}

📦 Product:
{p['name']}

💰 Amount:
৳{p['price']}

💳 Payment:
{method}

⏳ Status:
PENDING
""",
            reply_markup=main_menu()
        )

        await context.bot.send_message(
            ADMIN_ID,
            f"""
🔔 NEW PAYMENT

🧾 Order:
#{oid}

👤 User:
{u.full_name}

🆔 ID:
{u.id}

📦 Product:
{p['name']}

💰 Amount:
৳{p['price']}

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
                        callback_data=f"accept_order:{oid}"
                    ),

                    InlineKeyboardButton(
                        "❌ REJECT",
                        callback_data=f"reject_order:{oid}"
                    )
                ]
            ])
        )


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
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "admin",
            admin
        )
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

    # SABBIR MODE PRO PRICE LIST

    app.add_handler(
        CallbackQueryHandler(
            sabbir_pro_menu,
            pattern="^sabbir_pro_menu$"
        )
    )

    # PRODUCTS

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

    # NORMAL TEXT

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print(
        "SABBIR MODS SHOP BOT STARTED"
    )

    app.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
