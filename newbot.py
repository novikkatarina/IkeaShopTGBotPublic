import requests
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext, ApplicationBuilder, \
    CallbackQueryHandler


async def show_all(update: Update, context: CallbackContext):
    """
    Shows all items to the user.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    # Your logic to show all items
    await update.message.reply_text("Все товары")
    response = requests.get('http://storage/Product/GetProducts')
    data = response.json()
    text = ''
    for idx, item in enumerate(data):
        modified_item = {
            "item_id": idx + 1,
            "title": item["title"],
            "description": item["description"]
        }
        text += f'{modified_item["item_id"]} {modified_item["title"]}\n{item["description"]}\n\n'

    await update.message.reply_text(text)


async def filter_items(update: Update, context: CallbackContext):
    """
    Responds with InlineKeyboardButtons for filtering options.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    keyboard = [
        [
            InlineKeyboardButton("Кухня", callback_data="filter_kitchen"),
            InlineKeyboardButton("Спальня", callback_data="filter_bedroom"),
            InlineKeyboardButton("Ванная", callback_data="filter_bathroom"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите фильтр по комнатам", reply_markup=reply_markup)


async def add_to_cart(update: Update, context: CallbackContext):
    """
    Adds items to the user's cart.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    response = requests.get('http://storage/Product/GetProducts')
    if response.status_code != 200:
        await update.message.reply_text("Возникла ошибка при загрузке.")
        return

    items = response.json()

    keyboard = [[InlineKeyboardButton(item["title"], callback_data=f"item_{item['id']}")] for item in items]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Выберите товар, чтобы добавить его в корзину.", reply_markup=reply_markup)
    elif update.callback_query.message:
        await update.callback_query.message.reply_text("Выберите товар, чтобы добавить его в корзину.",
                                                       reply_markup=reply_markup)
    if "cart" not in context.user_data:
        context.user_data["cart"] = []


async def enter_quantity(update: Update, context: CallbackContext):
    """
    Asks the user to enter the quantity of items.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    keyboard = [[InlineKeyboardButton(str(item), callback_data=f"quantity_{item}")] for item in range(1, 9)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Введите количество товаров.", reply_markup=reply_markup)


async def create_order(update: Update, context: CallbackContext):
    """
    Creates an order based on the items in the user's cart.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    if 'cart' in context.user_data:
        response = requests.get('http://storage/Product/GetProducts')
        products = response.json()

        selected_items = []
        for cart_item in context.user_data['cart']:
            product = list(filter(lambda x: x['id'] == cart_item['id'], products))[0]
            selected_items.append({'id': cart_item['id'], 'title': product['title'], 'quantity': cart_item['quantity'],
                                   'price': product['price']})

        text = ''
        total = 0
        for idx, item in enumerate(selected_items):
            price = item["price"] * item["quantity"]
            text += f'{idx + 1} {item["title"]} Количество: {item["quantity"]} Цена: {price} \n'
            total += price
        text += f'Цена итого: {total}'

        await update.message.reply_text(text)
    else:
        await update.message.reply_text('Ничего не выбрано')


async def button(update: Update, context: CallbackContext):
    """
    Handles button clicks in the chat, including filter selection and item quantity selection.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    query = update.callback_query
    await query.answer()

    if query.data.startswith("filter_"):
        await handle_filter_selection(update, context)

    if query.data.startswith("item_"):
        splitted = query.data.split('_')
        context.user_data['current_item'] = {'id': splitted[1]}
        await enter_quantity(update, context)

    if query.data.startswith("quantity_"):
        splitted = query.data.split('_')
        context.user_data['current_item']['quantity'] = int(splitted[1])
        context.user_data['cart'].append(context.user_data['current_item'])
        await add_to_cart(update, context)


async def handle_filter_selection(update: Update, context: CallbackContext) -> None:
    """
    Handles filter selections and displays filtered product listings.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    query = update.callback_query
    await query.answer()

    if query.data == "filter_kitchen":
        response = requests.get('http://storage/Product/GetProducts')
        products = response.json()
        products = filter(lambda x: x['room'] == 0, products)
        await query.message.reply_text(
            f"Кухня: {', '.join([product['title'] for product in products])}")

    elif query.data == "filter_bedroom":
        response = requests.get('http://storage/Product/GetProducts')
        products = response.json()
        products = filter(lambda x: x['room'] == 1, products)
        await query.message.reply_text(
            f"Спальня: {', '.join([product['title'] for product in products])}")

    elif query.data == "filter_bathroom":
        response = requests.get('http://storage/Product/GetProducts')
        products = response.json()
        products = filter(lambda x: x['room'] == 2, products)
        await query.message.reply_text(
            f"Ванная: {', '.join([product['title'] for product in products])}")


async def start(update: Update, context: CallbackContext):
    """
    Handles the start command and displays the initial menu.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    keyboard = [
        [KeyboardButton("Показать все"),
         KeyboardButton("Фильтровать")],
        [KeyboardButton("Добавить в корзину"),
         KeyboardButton("Создать заказ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        'Здравствуйте! Я бот IkeaShop! Посетите наш сайт http://фурнитуре.рф/. Я готов вам помочь. Пожалуйста выберите действие:',
        reply_markup=reply_markup)


async def cancel(update: Update, context: CallbackContext):
    """
    Cancels the user's current cart and clears it.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    await update.message.reply_text("Ваша корзина была очищена")
    context.user_data["cart"] = []


async def handle_text_input(update: Update, context: CallbackContext):
    """
    Handles text input from the user and performs corresponding actions.

    Args:
        update (Update): The Telegram update.
        context (CallbackContext): The context for the callback.

    Returns:
        None
    """
    user_input = update.message.text

    if user_input == 'Показать все':
        await show_all(update, context)
    elif user_input == 'Фильтровать':
        await filter_items(update, context)
    elif user_input == 'Добавить в корзину':
        await add_to_cart(update, context)
    elif user_input == 'Создать заказ':
        await create_order(update, context)


def main():
    """
    The main function to run the Telegram bot.

    Returns:
        None
    """
    app = ApplicationBuilder().token("TOKEN").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler('items', show_all))
    app.add_handler(CommandHandler("filter", filter_items))
    app.add_handler(CommandHandler("order", create_order))
    app.add_handler(CommandHandler("additem", add_to_cart))
    app.add_handler(CommandHandler("cancel", cancel))

    app.run_polling()


if __name__ == '__main__':
    main()
