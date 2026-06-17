from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)
import credentials

chat_modes = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.effective_user.id] = 'DEFAULT'
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
    })





async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.effective_user.id] = 'RANDOM'
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, "Давай рандомний факт")
    await send_image(update, context, 'random')
    await send_text_buttons(update, context, response, {
        'random_finish': 'Закінчити',
        'random_one_more': 'Хочу ще факт'
    })


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.message.from_user.id] = 'GPT_MODE'
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message('gpt'))


async def talk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'talk')
    await send_text_buttons(update, context, load_message('talk'), {
        'talk_Cobain': 'Курт Кобейн',
        'talk_Elizabeth_II': 'Єлизавета II',
        'talk_Tolkien': 'Джон Толкін',
        'talk_Nietzsche': 'Фрідріх Ніцше',
        'talk_Hawking': 'Стівен Гокінг',
        'talk_finish': 'Головне меню'
    })


async def talk_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = chat_modes.get(update.effective_user.id)
    text =  update.message.text + 'Формулюй думки стисло, без зайвої води'
    response = await chat_gpt.send_question(load_prompt(mode), text)
    await send_text_buttons(
        update, context, response, {
            'talk_finish': 'Повернутись в головне меню'
        })


async def plain_text_handler(update: Update, context):
    mode = chat_modes.get(update.effective_user.id)
    text = update.message.text
    if mode in [None, 'DEFAULT']:
        if text == '/start':
            await start(update, context)
        elif text == '/random':
            await random(update, context)
        elif text == '/gpt':
            await gpt(update, context)
        elif text == '/talk':
            await talk_handler(update, context)
        else:
            await send_text(update, context, "I don't understand this team.")
    elif mode == 'GPT_MODE':
        pt = load_prompt('gpt')
        response = await chat_gpt.send_question(pt, update.message.text)
        await send_text_buttons(
            update, context, response, {
            'gpt_finish': 'Закінчити'
            })
    elif mode and mode.startswith('talk_'):
        await talk_chat_handler(update, context)



async def talk_buttons_handler(update: Update, context):
    query = update.callback_query.data
    user_id = update.callback_query.from_user.id
    if query == 'talk_finish':
        chat_modes[user_id] = 'DEFAULT'
        await start(update, context)
    elif query == 'talk_Cobain':
        chat_modes[user_id] = 'talk_cobain'
        await send_text(update, context, 'Ви спілкуєтесь з Курт Кобейн')
    elif query == 'talk_Elizabeth_II':
        chat_modes[user_id] = 'talk_queen'
        await send_text(update, context, 'Ви спілкуєтесь з Єлизаветою II')
    elif query == 'talk_Tolkien':
        chat_modes[user_id] = 'talk_tolkien'
        await send_text(update, context, 'Ви спілкуєтесь з Джон Толкін')
    elif query == 'talk_Nietzsche':
        chat_modes[user_id] = 'talk_nietzsche'
        await send_text(update, context, 'Ви спілкуєтесь з Фрідріх Ніцше')
    elif query == 'talk_Hawking':
        chat_modes[user_id] = 'talk_hawking'
        await send_text(update, context, 'Ви спілкуєтесь з Стівен Гокінг')
    await update.callback_query.answer()


async def random_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == 'random_finish':
        chat_modes[update.callback_query.from_user.id] = 'DEFAULT'
        await start(update, context)
    elif query == 'random_one_more':
        chat_modes[update.callback_query.from_user.id] = 'RANDOM'
        await random(update, context)
    await update.callback_query.answer()


async def gpt_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == 'gpt_finish':
        chat_modes[update.callback_query.from_user.id] = 'DEFAULT'
        await start(update, context)
    await update.callback_query.answer()


chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(MessageHandler(filters.TEXT, plain_text_handler))
# app.add_handler(CommandHandler('start', start))
# app.add_handler(CommandHandler('random', random))
# app.add_handler(CommandHandler('gpt', gpt))


# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_buttons_handler, pattern='^talk_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
