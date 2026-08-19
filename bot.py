import logging
from datetime import time
import pytz
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# --- 1. Render ቦቱ እንዳይተኛ የሚያደርገው የ Flask ክፍል ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def keep_alive():
    app.run(host='0.0.0.0', port=8080)

# Flask ን በጀርባ (Background Thread) ማስነሳት
threading.Thread(target=keep_alive, daemon=True).start()

# --- 2. የቦቱ ዋና ኮድ ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TIMEZONE = pytz.timezone('Africa/Addis_Ababa')

ETHIOPIAN_MONTHS = [
    "መስከረም", "ጥቅምት", "ኅዳር", "ታኅሣሥ", 
    "ጥር", "የካቲት", "መጋቢት", "ሚያዝያ", 
    "ግንቦት", "ሰኔ", "ሐምሌ", "ነሐሴ"
]

DB = {
    "admins": [829583750],          # የእርስዎ Telegram ID
    "executives": set([829583750]), # የስራ አስፈፃሚዎች ID
    "meeting_link": "https://zoom.us/j/example",
    "announcement": "እስካሁን ምንም አዲስ ማስታወቂያ አልተለቀቀም።",
    "members": {}  
}

PROGRAM_SCHEDULE = (
    "📌 **የስብሰባ እና የፀሎት ፕሮግራሞች፦**\n\n"
    "• **እሮብ ማታ 3:00** - የስራ አስፈፃሚ (በZoom/Telegram)\n"
    "• **አርብ ከቀኑ 11:30** - የማ/ቅ መደበኛ የአርብ ፀሎት\n"
    "• **እሁድ ጠዋት 1:40** - የስራ አስፈፃሚ (በጽህፈት ቤት)\n"
)

# --- START & REGISTRATION ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.full_name
    
    if user_id not in DB["members"]:
        DB["members"][user_id] = {
            "name": name,
            "attendance": [],
            "absent_count": 0,
            "monthly_fee": {m: "❌" for m in ETHIOPIAN_MONTHS},
            "social_fee": {m: "❌" for m in ETHIOPIAN_MONTHS}
        }

    if user_id in DB["admins"]:
        keyboard = [
            ["📋 አቴንዳንስ", "💰 ወርሃዊ ክፍያ"],
            ["🤝 ማህበራዊ አስተዋፅኦ", "📊 ሙሉ ሮስተር"],
            ["📢 ማስታወቂያ", "🔗 የስብሰባ ሊንክ"],
            ["📅 የስብሰባ ፕሮግራሞች", "👤 ስራ አስፈፃሚ መመዝገቢያ"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"ሰላም አድሚን **{name}**!\n\n{PROGRAM_SCHEDULE}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        keyboard = [
            ["📅 የስብሰባ ፕሮግራሞች", "🔗 የስብሰባ ሊንክ"],
            ["📢 ማስታወቂያዎች", "👤 የእኔ መረጃ"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"ሰላም **{name}**! በስም መዝገቡ ላይ ተመዝግበዋል።\n\n{PROGRAM_SCHEDULE}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# --- TEXT MENU HANDLER ---

async def handle_amharic_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "📅 የስብሰባ ፕሮግራሞች":
        await update.message.reply_text(PROGRAM_SCHEDULE, parse_mode="Markdown")

    elif text == "🔗 የስብሰባ ሊንክ":
        await update.message.reply_text(
            f"🔗 **የአሁኑ የስብሰባ ሊንክ (Zoom / Telegram Voice Chat)፦**\n{DB['meeting_link']}", 
            parse_mode="Markdown"
        )

    elif text in ["📢 ማስታወቂያዎች", "📢 ማስታወቂያ"]:
        if user_id in DB["admins"]:
            await update.message.reply_text(
                f"📢 **ማስታወቂያ ለመልቀቅ፦** `/post የማስታወቂያው ጽሁፍ`\n\n**የአሁኑ፦** {DB['announcement']}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"📢 **አዲስ ማስታወቂያ፦**\n\n{DB['announcement']}", parse_mode="Markdown")

    elif text == "👤 የእኔ መረጃ":
        m_data = DB["members"].get(user_id, {})
        
        att_list = m_data.get("attendance", [])
        att_str = ", ".join(att_list) if att_list else "ምንም አልተመዘገበም"
        
        m_fee_str = ", ".join([f"{m}:{s}" for m, s in m_data.get("monthly_fee", {}).items()])
        s_fee_str = ", ".join([f"{m}:{s}" for m, s in m_data.get("social_fee", {}).items()])
        
        msg = (
            f"👤 **ስም፦** {m_data.get('name', '')}\n\n"
            f"📋 **የአርብ አቴንዳንስ፦**\n`[{att_str}]`\n\n"
            f"💰 **ወርሃዊ ክፍያ፦**\n`{m_fee_str}`\n\n"
            f"🤝 **ማህበራዊ አስተዋፅኦ፦**\n`{s_fee_str}`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text in ["📋 አቴንዳንስ", "📋 አቴንዳንስ መመዝገቢያ"] and user_id in DB["admins"]:
        await show_attendance_menu(update, context)

    elif text == "💰 ወርሃዊ ክፍያ" and user_id in DB["admins"]:
        await show_fee_member_select(update, context, "m")

    elif text == "🤝 ማህበራዊ አስተዋፅኦ" and user_id in DB["admins"]:
        await show_fee_member_select(update, context, "s")

    elif text == "📊 ሙሉ ሮስተር" and user_id in DB["admins"]:
        await view_full_roster(update, context)

    elif text == "👤 ስራ አስፈፃሚ መመዝገቢያ" and user_id in DB["admins"]:
        await update.message.reply_text("ስራ አስፈፃሚ ለመመዝገብ፦ `/addexec <USER_ID>`", parse_mode="Markdown")

# --- INTERACTIVE FEE MANAGEMENT (BUTTON-BASED) ---

async def show_fee_member_select(update: Update, context: ContextTypes.DEFAULT_TYPE, fee_type: str):
    if not DB["members"]:
        return await update.message.reply_text("ምንም የተመዘገበ አባል የለም።")

    keyboard = []
    for m_id, m_data in DB["members"].items():
        keyboard.append([InlineKeyboardButton(f"👤 {m_data['name']}", callback_data=f"feemem_{fee_type}_{m_id}")])

    title = "💰 **የወርሃዊ ክፍያ ለመመዝገብ አባል ይምረጡ፦**" if fee_type == "m" else "🤝 **የማህበራዊ አስተዋፅኦ ክፍያ ለመመዝገብ አባል ይምረጡ፦**"
    await update.message.reply_text(title, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def render_member_months_keyboard(query, fee_type: str, user_id: int):
    m_data = DB["members"].get(user_id)
    if not m_data:
        return await query.edit_message_text("አባሉ አልተገኘም።")

    fee_key = "monthly_fee" if fee_type == "m" else "social_fee"
    fees = m_data[fee_key]

    keyboard = []
    row = []
    for idx, month in enumerate(ETHIOPIAN_MONTHS):
        status = fees.get(month, "❌")
        row.append(InlineKeyboardButton(f"{month} {status}", callback_data=f"feetog_{fee_type}_{user_id}_{idx}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ ወደ አባላት ዝርዝር ተመለስ", callback_data=f"feemenu_{fee_type}")])

    fee_name = "ወርሃዊ ክፍያ" if fee_type == "m" else "ማህበራዊ አስተዋፅኦ"
    text = (
        f"👤 **አባል፦ {m_data['name']}**\n"
        f"📌 **ዓይነት፦ {fee_name}**\n\n"
        f"💡 ወሩን በመጫን የክፍያ ሁኔታውን ይቀይሩ፦\n"
        f"• **✔️** = የተከፈለ\n"
        f"• **❌** = ያልተከፈለ\n"
        f"• **P** = በፍቃድ\n"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- ADMIN COMMANDS ---

async def set_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in DB["admins"]:
        return
    if context.args:
        DB["meeting_link"] = context.args[0]
        await update.message.reply_text(f"✅ የስብሰባ ሊንክ ተቀይሯል፦ {DB['meeting_link']}")
        for m_id in DB["members"].keys():
            try:
                await context.bot.send_message(
                    chat_id=m_id, 
                    text=f"🔗 **አዲስ የስብሰባ ሊንክ ተለቋል፦**\n{DB['meeting_link']}\n\nእባክዎን በዚህ ሊንክ ይግቡ።", 
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Link send error: {e}")
    else:
        await update.message.reply_text("አጠቃቀም፦ `/setlink https://zoom.us/j/your_link`", parse_mode="Markdown")

async def add_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in DB["admins"]:
        return
    try:
        exec_id = int(context.args[0])
        DB["executives"].add(exec_id)
        await update.message.reply_text(f"✅ User ID `{exec_id}` በስራ አስፈፃሚነት ተመዝግቧል።", parse_mode="Markdown")
    except:
        await update.message.reply_text("አጠቃቀም፦ `/addexec <USER_ID>`", parse_mode="Markdown")

async def post_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in DB["admins"]:
        return
    if context.args:
        announcement_text = " ".join(context.args)
        DB["announcement"] = announcement_text
        await update.message.reply_text("✅ ማስታወቂያው ተለቋል!")
        for m_id in DB["members"].keys():
            try:
                await context.bot.send_message(chat_id=m_id, text=f"📢 **አዲስ ማስታወቂያ፦**\n\n{announcement_text}", parse_mode="Markdown")
            except Exception as e:
                print(f"Error: {e}")

# --- ATTENDANCE & ROSTER DISPLAYS ---

async def show_attendance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DB["members"]:
        return await update.message.reply_text("ምንም የተመዘገበ አባል የለም።")

    text = "📋 **የአርብ አቴንዳንስ የስም መዝገብ (Roster)፦**\n\n"
    keyboard = []
    
    for m_id, m_data in DB["members"].items():
        att_str = " ".join(m_data["attendance"][-5:]) if m_data["attendance"] else "ምንም"
        text += f"👤 **{m_data['name']}**\n    └ አቴንዳንስ፦ [{att_str}]\n"
        keyboard.append([
            InlineKeyboardButton(f"✔️ {m_data['name'][:10]}", callback_data=f"att_{m_id}_check"),
            InlineKeyboardButton("❌ የቀረ", callback_data=f"att_{m_id}_x"),
            InlineKeyboardButton("P በፍቃድ", callback_data=f"att_{m_id}_p")
        ])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def view_full_roster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DB["members"]:
        return await update.message.reply_text("ምንም የተመዘገበ አባል የለም።")

    text = "📊 **የአባላት አጠቃላይ የ12ቱ ወራት ሮስተር፦**\n\n"
    for m_id, m_data in DB["members"].items():
        m_paid = sum(1 for s in m_data["monthly_fee"].values() if s == "✔️")
        s_paid = sum(1 for s in m_data["social_fee"].values() if s == "✔️")
        att_str = " ".join(m_data["attendance"]) if m_data["attendance"] else "ምንም"
        
        text += (
            f"👤 **ስም፦ {m_data['name']}** (ID: `{m_id}`)\n"
            f"    • አቴንዳንስ፦ [{att_str}]\n"
            f"    • ወርሃዊ ክፍያ፦ {m_paid}/12 ወር\n"
            f"    • ማህበራዊ አስተዋፅኦ፦ {s_paid}/12 ወር\n"
            f"-----------------------------------\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

# --- COMBINED BUTTON CALLBACK HANDLER ---

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data

    # 1. ATTENDANCE BUTTONS
    if data.startswith("att_"):
        parts = data.split("_")
        user_id = int(parts[1])
        action = parts[2]

        if user_id not in DB["members"]:
            return await query.edit_message_text("አባሉ አልተገኘም።")

        if action == "check":
            mark = "✔️"
            DB["members"][user_id]["absent_count"] = 0
        elif action == "p":
            mark = "P"
            DB["members"][user_id]["absent_count"] = 0
        elif action == "x":
            mark = "❌"
            DB["members"][user_id]["absent_count"] += 1
            if DB["members"][user_id]["absent_count"] >= 2:
                warning_msg = f"⚠️ **ማስጠንቀቂያ፦** ሰላም {DB['members'][user_id]['name']}፤ በተከታታይ 2 ሳምንት ከአርብ ፀሎት ስለቀሩ ምክንያቱን ያሳውቁ!"
                try:
                    await context.bot.send_message(chat_id=user_id, text=warning_msg, parse_mode="Markdown")
                except Exception as e:
                    print(f"Error: {e}")

        DB["members"][user_id]["attendance"].append(mark)
        await query.message.reply_text(f"የ **{DB['members'][user_id]['name']}** አቴንዳንስ በ '{mark}' ተመዝግቧል።", parse_mode="Markdown")

    # 2. FEE MEMBER SELECT
    elif data.startswith("feemenu_"):
        fee_type = data.split("_")[1]
        keyboard = []
        for m_id, m_data in DB["members"].items():
            keyboard.append([InlineKeyboardButton(f"👤 {m_data['name']}", callback_data=f"feemem_{fee_type}_{m_id}")])
        title = "💰 **የወርሃዊ ክፍያ ለመመዝገብ አባል ይምረጡ፦**" if fee_type == "m" else "🤝 **የማህበራዊ አስተዋፅኦ ክፍያ ለመመዝገብ አባል ይምረጡ፦**"
        await query.edit_message_text(title, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 3. SHOW MONTHS FOR SELECTED MEMBER
    elif data.startswith("feemem_"):
        parts = data.split("_")
        fee_type = parts[1]
        user_id = int(parts[2])
        await render_member_months_keyboard(query, fee_type, user_id)

    # 4. TOGGLE MONTH STATUS
    elif data.startswith("feetog_"):
        parts = data.split("_")
        fee_type = parts[1]
        user_id = int(parts[2])
        month_idx = int(parts[3])

        m_data = DB["members"].get(user_id)
        if m_data:
            fee_key = "monthly_fee" if fee_type == "m" else "social_fee"
            month = ETHIOPIAN_MONTHS[month_idx]
            current_status = m_data[fee_key].get(month, "❌")

            # Toggle sequence: ❌ -> ✔️ -> P -> ❌
            if current_status == "❌":
                new_status = "✔️"
            elif current_status == "✔️":
                new_status = "P"
            else:
                new_status = "❌"

            m_data[fee_key][month] = new_status
            await render_member_months_keyboard(query, fee_type, user_id)

# --- AUTOMATIC NOTIFICATIONS ---

async def remind_wednesday_meeting(context: ContextTypes.DEFAULT_TYPE):
    msg = f"ማታ 3፡00 ስብሰባ አለ ይህን ሊንክ / join ይበሉ፦\n{DB['meeting_link']}"
    for exec_id in DB["executives"]:
        try:
            await context.bot.send_message(chat_id=exec_id, text=msg)
        except Exception as e:
            print(f"Wednesday reminder error: {e}")

async def remind_sunday_meeting(context: ContextTypes.DEFAULT_TYPE):
    msg = "ከጠዋቱ 1፡40 ስብሰባ ስላለ በፅህፈት ቤት ይገኙ"
    for exec_id in DB["executives"]:
        try:
            await context.bot.send_message(chat_id=exec_id, text=msg)
        except Exception as e:
            print(f"Sunday reminder error: {e}")

async def remind_friday_meeting(context: ContextTypes.DEFAULT_TYPE):
    msg = "ማስታወሻ፦ ዛሬ አርብ ከቀኑ 11፡30 ጀምሮ የማ/ቅ መደበኛ የአርብ ፀሎት ስላለ በሰዓቱ እንድትገኙ።"
    for user_id in DB["members"].keys():
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
        except Exception as e:
            print(f"Friday reminder error: {e}")

async def remind_monthly_fees(context: ContextTypes.DEFAULT_TYPE):
    msg = "ማስታወሻ፦ እባክዎን የወርሃዊ እና የማህበራዊ አስተዋፅኦ ክፍያዎን በወቅቱ ይክፈሉ።"
    for user_id in DB["members"].keys():
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
        except Exception as e:
            print(f"Fee reminder error: {e}")

# --- MAIN RUNNER ---

def main():
    TOKEN = "8604604908:AAFHJNE2WZDTbA1JhSJOBNWk2WNzeT9XnCY"
    
    app_bot = ApplicationBuilder().token(TOKEN).build()
    job_queue = app_bot.job_queue

    # Schedules
    job_queue.run_daily(remind_wednesday_meeting, time=time(hour=20, minute=55, tzinfo=TIMEZONE), days=(2,))
    job_queue.run_daily(remind_sunday_meeting, time=time(hour=7, minute=35, tzinfo=TIMEZONE), days=(6,))
    job_queue.run_daily(remind_friday_meeting, time=time(hour=17, minute=30, tzinfo=TIMEZONE), days=(4,))
    job_queue.run_monthly(remind_monthly_fees, when=time(hour=9, minute=0, tzinfo=TIMEZONE), day=1)

    # Handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("post", post_announcement))
    app_bot.add_handler(CommandHandler("setlink", set_link))
    app_bot.add_handler(CommandHandler("addexec", add_exec))

    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amharic_menu))
    app_bot.add_handler(CallbackQueryHandler(handle_callback_query))

    print("ቦቱ በስኬት ስራ ጀምሯል...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()