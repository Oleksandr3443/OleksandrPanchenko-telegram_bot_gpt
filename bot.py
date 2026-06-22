from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)


import credentials

chat_modes = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.effective_user.id] = {'mode': 'DEFAULT'}
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
    chat_modes[update.effective_user.id] = {'mode': 'RANDOM'}
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, "Давай рандомний факт")
    await send_image(update, context, 'random')
    await send_text_buttons(update, context, response, {
        'random_finish': 'Закінчити',
        'random_one_more': 'Хочу ще факт'
    })


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.message.from_user.id] = {'mode': 'GPT_MODE'}
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
    # mode = chat_modes.get(update.effective_user.id)
    state = chat_modes.get(update.effective_user.id, {})
    mode = state.get("mode")
    text =  update.message.text + 'Формулюй думки стисло, без зайвої води'
    response = await chat_gpt.send_question(load_prompt(mode), text)
    await send_text_buttons(
        update, context, response, {
            'talk_finish': 'Повернутись в головне меню'
        })


async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'quiz')
    await send_text_buttons(update, context, load_message('quiz'), {
         'quiz_prog': 'Програмування мовою python',
         'quiz_math': 'Дискретна математика',
         'quiz_biology': 'Біологія',
         'quiz_finish': 'Головне меню'
    })

async def quiz_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = chat_modes.get(update.effective_user.id, {})
    topic = state.get('selected_topic')
    response = await chat_gpt.send_question(
        load_prompt('quiz'),
        f"Тема: {topic}. Перевір відповідь: {update.message.text}. Відповідай тільки Правильно або Неправильно")
    if 'Правильно!' in response:
        context.user_data['points'] += 1
    await send_text_buttons(update, context, response, {
            'quiz_more': 'Ще питання поточної теми',
            'quiz_restart': 'Повернутись до вибору тем',
            'quiz_finish': 'Повернутись в головне меню'
            })
    await send_text(update, context, f"Поточний рахунок: {context.user_data['points']}")


async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = chat_modes.get(update.effective_user.id, {})
    topic = state.get("selected_topic")
    first_question = await chat_gpt.send_question(
        load_prompt('quiz'),
        f"Згенеруй питання по темі {topic}. Коротке. Без варіантів відповіді.")
    await send_text_buttons(update, context, first_question, {
        'quiz_more': "Ще питання поточної теми",
        'quiz_restart': "Повернутись до вибору тем",
        'quiz_finish': "Головне меню"
    })


async def plain_text_handler(update: Update, context):
    user_id = update.effective_user.id
    state = chat_modes.get(user_id, {})
    mode = state.get("mode")
    topic = state.get("selected_topic")
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
        elif text == '/quiz':
            await quiz_handler(update, context)
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
    elif mode == "QUIZ":
        await quiz_request_handler(update, context)


async def quiz_buttons_handler(update: Update, context):
    query = update.callback_query.data
    user_id = update.callback_query.from_user.id
    if query.startswith('quiz_') and query not in ['quiz_more', 'quiz_restart', 'quiz_finish']:
        context.user_data.setdefault('points', 0)
        chat_modes[user_id] = {
            "mode": "QUIZ",
            "selected_topic": query}
        topic = chat_modes.get(user_id, {}).get("selected_topic")
        first_question = await chat_gpt.send_question(load_prompt('quiz'), topic)
        await send_text_buttons(update, context, first_question, {
                    'quiz_finish': 'Повернутись в головне меню'
                })
    else:
        if query == 'quiz_more':
            await send_quiz_question(update, context)
        elif query == 'quiz_restart':
            await quiz_handler(update, context)
        elif query == 'quiz_finish':
            await start(update, context)
    await update.callback_query.answer()


async def talk_buttons_handler(update: Update, context):
    query = update.callback_query.data
    user_id = update.callback_query.from_user.id
    state = chat_modes.setdefault(user_id, {})
    if query == 'talk_finish':
        state['mode'] = 'DEFAULT'
        await start(update, context)
    elif query == 'talk_Cobain':
        state['mode'] = 'talk_cobain'
        await send_text(update, context, 'Ви спілкуєтесь з Курт Кобейн')
    elif query == 'talk_Elizabeth_II':
        state['mode'] = 'talk_queen'
        await send_text(update, context, 'Ви спілкуєтесь з Єлизаветою II')
    elif query == 'talk_Tolkien':
        state['mode'] = 'talk_tolkien'
        await send_text(update, context, 'Ви спілкуєтесь з Джон Толкін')
    elif query == 'talk_Nietzsche':
        state['mode'] = 'talk_nietzsche'
        await send_text(update, context, 'Ви спілкуєтесь з Фрідріх Ніцше')
    elif query == 'talk_Hawking':
        state['mode'] = 'talk_hawking'
        await send_text(update, context, 'Ви спілкуєтесь з Стівен Гокінг')
    await update.callback_query.answer()


async def random_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == 'random_finish':
        chat_modes[update.callback_query.from_user.id] = {'mode': 'DEFAULT'}
        await start(update, context)
    elif query == 'random_one_more':
        chat_modes[update.callback_query.from_user.id] = {'mode': 'RANDOM'}
        await random(update, context)
    await update.callback_query.answer()


async def gpt_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == 'gpt_finish':
        chat_modes[update.callback_query.from_user.id] = {'mode': 'DEFAULT'}
        await start(update, context)
    await update.callback_query.answer()


chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()


app.add_handler(MessageHandler(filters.TEXT, plain_text_handler))
# app.add_handler(CommandHandler('start', start))
# app.add_handler(CommandHandler('random', random))
# app.add_handler(CommandHandler('gpt', gpt))


app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_buttons_handler, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern='^quiz_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()