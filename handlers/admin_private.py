from aiogram import F , Router , types
import aiosqlite
import base64

from aiogram.filters import Command
from filters.chat_types import ChatTypeFilter, IsAdmin
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from database.engine import delete, show_something, add_something, add_photo, create_category, get_all_categories, delete_category, set_shop_status
from keyboards.keyboard import meun , admin_menu, del_smth
from aiogram import F
from aiogram import Router, types
from aiogram.filters import BaseFilter
from bot_main import ADMINS, DB_PATH
import datetime
import asyncio


admin_private_router = Router()

# Фільтр для перевірки, чи користувач адмін
class IsAdmin(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMINS


# Команда для додавання себе в адміни
@admin_private_router.message(Command("makeadmin"))
async def make_admin(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    if user_id in ADMINS:
        await message.answer("👑 Ти вже адміністратор.")
        return

    ADMINS.append(user_id)
    await message.answer(f"✅ @{username or 'Без_ніка'} тепер адміністратор!")


# Стартова команда адмінки
@admin_private_router.message(Command("adminmenu"), IsAdmin())
async def start_admin_panel(message: Message):
    await message.answer(
        "👋 Адмін панель ДУІКТ МАРКЕТ. Всі функції для роботи тут:",reply_markup=admin_menu
        
    )





###################################################################################################################
###################################################################################################################
@admin_private_router.message(F.text == "Видалити товар")
async def choose_category(message: Message):
   
    categories = await get_all_categories()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text = f"{cat}", callback_data=f"choose_{cat}")
            
            ]for cat in categories
        ]
    )
    await message.answer(
    "delete old keyboard ",
        reply_markup= del_smth
    )

    await message.answer(
        "🗑 <b>Оберіть категорію:</b>",
        reply_markup=inline_kb,
        
        parse_mode="HTML"
    )



@admin_private_router.callback_query(F.data.startswith("choose_"))
async def choose_id(callback: CallbackQuery):
    category = callback.data.replace("choose_", "")
    show = await show_something(category)
    if not show:
        await callback.message.answer(f"⚠️ У категорії <b>{category}</b> поки що немає товарів.", parse_mode="HTML")
        return

    inline_product = InlineKeyboardMarkup(
        inline_keyboard=[
            [
            InlineKeyboardButton(text = name, callback_data=f"show_{category}_{row_id}")
            ]
            for row_id, name, *_ in show
            
            ]
        
    )
    await callback.message.answer(
        f"📦 <b>{category}</b>\nОберіть товар для видалення:",

        parse_mode="HTML",
        reply_markup=inline_product
    )

@admin_private_router.callback_query(F.data.startswith("show_"))
async def work_with_one(callback: CallbackQuery):
    parts = callback.data.split("_")
    _, category, product_id = parts
    product_id = int(product_id)
    products = await show_something(category)

    selected = next((p for p in products if p[0] == product_id), None)

    if not selected:
        await callback.answer("❌ Товар не знайдено.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Так, видалити",
                callback_data=f"confirm_delete|yes|{category}|{product_id}"
            ),
            InlineKeyboardButton(
                text="❌ Ні, скасувати",
                callback_data=f"confirm_delete|no|{category}|{product_id}"
            )
        ]
    ])

    await callback.message.answer(
        f"Ви дійсно хочете видалити товар із категорії <b>{category}</b> (ID: {product_id})?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@admin_private_router.callback_query(F.data.startswith("confirm_delete"))
async def process_delete(callback: CallbackQuery):
    parts = callback.data.split("|")

    if len(parts) < 4:
        await callback.answer(" Невірні дані для видалення.", show_alert=True)
        return

    _, action, category, product_id = parts
    product_id = int(product_id)

    if action == "yes":
        try:
            await delete(category, product_id)
            await callback.message.edit_text(
                f"✅ Товар із категорії <b>{category}</b> успішно видалено.",
                parse_mode="HTML"
            )
        except Exception as e:
            await callback.message.answer(f"⚠️ Помилка при видаленні: {e}")
    else:
        await callback.message.edit_text("❎ Видалення скасовано.")

###################################################################################################################
###################################################################################################################


###################################################################################################################
###################################################################################################################




class Add_Product(StatesGroup):
    name = State()
    category = State()
    price = State()
    
    quantity = State()
    image = State()


@admin_private_router.message(F.text == "Додати товар")
async def choose_category(message: Message):
       
    categories = await get_all_categories()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text = f"{cat}", callback_data=f"chose_{cat}")
            
            ]for cat in categories
        ]
    )
    await message.answer(
    "delete old keyboard ",
        reply_markup= del_smth
    )

    await message.answer(
        "🗑 <b>Оберіть категорію:</b>",
        reply_markup=inline_kb,
        
        parse_mode="HTML"
    )

@admin_private_router.callback_query(F.data.startswith("chose_"))
async def choose_id(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace("chose_", "")
    
    
    await state.update_data(category = category)
    await state.set_state(Add_Product.name)
    await callback.message.answer(
        f"✅ Обрано категорію: <b>{category}</b>\nОберіть назву товару: ",
        parse_mode="HTML"
    )

@admin_private_router.message(StateFilter('*'), Command("відміна"))
@admin_private_router.message(StateFilter('*'), F.text.casefold()== "відміна")
async def cancel(message: types.Message, state: FSMContext):
    await state.clear
    await message.answer(" Додавання товару скасовано.", reply_markup=admin_menu)


@admin_private_router.message(StateFilter('*'), Command("назад"))
@admin_private_router.message(StateFilter('*'), F.text.casefold()== "назад")
async def exit(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    

    all_states = list(Add_Product.__all_states__)
    try:
        index = all_states.index(current_state)
    except ValueError:
        await message.answer("Неможливо повернутися назад.")
        return
    
    if index == 0:
        await message.answer("Повернення назад неможливе.", reply_markup=admin_menu)
        return
    
    previous_state = all_states[index - 1]
    await state.set_state(previous_state)
    await message.answer(f"Повернення назад.\n{Add_Product.promts[previous_state]}", reply_markup=admin_menu)

@admin_private_router.message(Add_Product.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name = message.text)
    await state.set_state(Add_Product.price)
    await message.answer("Введіть ціну товару:") 


@admin_private_router.message(Add_Product.price)
async def process_price(message: Message, state: FSMContext):
    await state.update_data(price = message.text)
    await state.set_state(Add_Product.quantity)
    await message.answer("Введіть кількість товару:") 


@admin_private_router.message(Add_Product.quantity)
async def process_price(message: Message, state: FSMContext):
    await state.update_data(quantity = message.text)
    await state.set_state(Add_Product.image)
    await message.answer("Завантажте фото товару:")  


@admin_private_router.message(Add_Product.image, F.photo)
async def process_photo(message: types.Message , state: FSMContext):
    await state.update_data(image = message.photo[-1].file_id)
    data = await state.get_data() 

    try:
        await add_something(data["category"], data)
        
        await message.answer("✅ Товар успішно додано до бази даних.", reply_markup=admin_menu)
    except Exception as e:
        await message.answer(f"⚠️ Помилка при додаванні товару: {e}", reply_markup=admin_menu)
    
    await state.clear()

###################################################################################################################
###################################################################################################################


###################################################################################################################
###################################################################################################################

class Add_Photo(StatesGroup):
    product_id = State()
    product_category = State
    product_photo = State()


@admin_private_router.message(F.text == "Додати фото")
async def chooose_category(message: Message):
    categories = await get_all_categories()

    inline_kb1 = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text = f"{cat}", callback_data=f"chi_{cat}")
               
            ]for cat in categories
        ]
    )

    await message.answer(
    "delete old keyboard ",
        reply_markup= del_smth
    )

    await message.answer(
        "🗑 <b>Оберіть категорію:</b>",
        reply_markup=inline_kb1,
        
        parse_mode="HTML"
    )

@admin_private_router.callback_query(F.data.startswith("chi_"))
async def choose_product(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace("chi_", "")
    
    show = await show_something(category)
    if not show:
        await callback.message.answer(f"⚠️ У категорії <b>{category}</b> поки що немає товарів.", parse_mode="HTML")
        return

    inline_product = InlineKeyboardMarkup(
        inline_keyboard=[
            [
            InlineKeyboardButton(text = name, callback_data=f"shiw_{category}_{row_id}")
            ]
            for row_id, name, *_ in show
            
            ]
    )
    await callback.message.answer(
        f"📦 <b>{category}</b>\nОберіть товар додавання фото для нього:",

        parse_mode="HTML",
        reply_markup=inline_product
    )

@admin_private_router.callback_query(F.data.startswith("shiw_"))
async def work_with_one(callback: CallbackQuery, state: FSMContext):
    data = callback.data.replace("shiw_", "")
    
    
    category, product_id = data.rsplit("_", 1)  
    product_id = int(product_id)
    
    await state.update_data(product_id=product_id, product_category=category)
    products = await show_something(category)

    selected = next((p for p in products if p[0] == product_id), None)

    if not selected:
        await callback.answer(" Товар не знайдено.", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Так, додати фото",
                callback_data=f"confirm_photo|yes|{category}|{product_id}"
            ),
            InlineKeyboardButton(
                text="❌ Ні, скасувати",
                callback_data=f"confirm_photo|no|{category}|{product_id}"
            )
        ]
    ])
    await callback.message.answer(
        f"Ви дійсно хочете додати фото для товару із категорії <b>{category}</b> (ID: {product_id})?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@admin_private_router.callback_query(F.data.startswith("confirm_photo"))
async def process_add(callback: CallbackQuery, state: FSMContext):
    action, answer, category, product_id = callback.data.split("|")
    if answer == "yes":
        await state.update_data(product_category=category, product_id=product_id)
        await state.set_state(Add_Photo.product_photo)
        await callback.message.answer("Надішліть фото для цього товару:")
    else:
        await callback.message.answer("Додавання фото скасовано")
        await state.clear()


@admin_private_router.message(F.photo, StateFilter(Add_Photo.product_photo))
async def add_photo_now(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id

    # Зберігаємо фото у FSMContext
    await state.update_data(product_photo=photo_id)
    data = await state.get_data()
    
    category = data.get("product_category")
    product_id = data.get("product_id")
    photo_id = data.get("product_photo")

    if not category or not product_id or not photo_id:
        await message.answer("❌ Сталася помилка. Неможливо зберегти фото.")
        await state.clear()
        return

    await add_photo(data, photo_id)

    await message.answer(
        f"Фото для товару з ID {product_id} у категорії <b>{category}</b> збережено ✅",
        parse_mode="HTML"
    )
    await state.clear()



class Add_category(StatesGroup):
    category = State()

@admin_private_router.message(F.text == "Додати категорію")
async def ask_category(message: Message, state: FSMContext):
    await message.answer("Введи назву категорії")
    await state.set_state(Add_category.category)


@admin_private_router.message(Add_category.category)
async def ad_category(message: Message, state:FSMContext):
    category_name = message.text.strip()
    await state.update_data(category = category_name)
    data = await state.get_data()

    try:
        await create_category(data["category"])
        categories = await get_all_categories()
        kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text = cat, callback_data=f"ch_{cat}")
            ]for cat in categories
        ]
    )
        await message.answer("✅ Категорію успішно додано до бази даних.", reply_markup=admin_menu)
    except Exception as e:
        await message.answer(f"⚠️ Помилка при додаванні категорії: {e}", reply_markup=admin_menu)

    await state.clear()
 
class Delete_category(StatesGroup):
    category = State()

@admin_private_router.message(F.text == "Видалити категорію")
async def ask_category(message: Message, state: FSMContext):
    await message.answer("Введи назву категорії")
    await state.set_state(Delete_category.category)


@admin_private_router.message(Delete_category.category)
async def del_category(message: Message, state:FSMContext):
    category_name = message.text.strip()
    await state.update_data(category = category_name)
    data = await state.get_data()

    try:
        await delete_category(data["category"])
        categories = await get_all_categories()
        kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text = cat, callback_data=f"ch_{cat}")
            ]for cat in categories
        ]
    )
        await message.answer("✅ Категорію успішно видалено з бази даних.", reply_markup=admin_menu)
    except Exception as e:
        await message.answer(f"⚠️ Помилка при додаванні категорії: {e}", reply_markup=admin_menu)

    await state.clear()


##############################################################################################################################################################################
###########################################################################################################################################################################

                                                                                                                                  

##############################################################################################################################################################################
##############################################################################################################################################################################


class Change_info(StatesGroup):
    category = State()
    product_name = State()
    edit = State()
    value = State()


@admin_private_router.message(F.text == "Змінити товар")
async def find_category(message:Message, state: FSMContext):
    categories = await get_all_categories()
    kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=cat,
                callback_data=f"chosoe_{base64.urlsafe_b64encode(cat.encode()).decode()}"
            )
        ] for cat in categories
    ]
)

    await message.answer(
    "🗑 <b>Оберіть категорію:</b>",
    reply_markup=kb,
        
    parse_mode="HTML"
    )



@admin_private_router.callback_query(F.data.startswith("chosoe_"))
async def find_product(callback: CallbackQuery, state: FSMContext):
    safe_cat = callback.data.replace("chosoe_", "")
    category = base64.urlsafe_b64decode(safe_cat.encode()).decode()
    await state.update_data(category=category)  # ✅ Зберігаємо в state

    show = await show_something(category)
    if not show:
        await callback.message.answer("Така категорія наразі недоступна")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=str(name),
                    callback_data=f"d_{row_id}"  
                )
            ] for row_id, name, *_ in show  
        ]
    )

    text = f"📦 <b>{category}</b>\nОберіть товар для зміни інформації:"
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@admin_private_router.callback_query(F.data.startswith("d_"))
async def select_product(callback: CallbackQuery, state: FSMContext):
   
    product_id = int(callback.data.replace("d_", ""))
    
    # Отримуємо category зі state
    data = await state.get_data()
    category = data.get("category")
    
    if not category:
        await callback.answer("❌ Помилка: категорія не знайдена.", show_alert=True)
        return

    products = await show_something(category)
    await state.update_data(product_name=product_id)  # ✅ Виправив назву

    selected = next((p for p in products if p[0] == product_id), None)  # ✅ ID - це перший елемент!
    
    if not selected:
        await callback.answer("❌ Товар не знайдено.", show_alert=True)
        return

    row_id, name, price, *_ = selected  # Розпаковуємо

    await callback.message.answer("Яке поле хочете відредагувати?(Назва товару / Ціна / Кількість):")
    await state.set_state(Change_info.edit)


@admin_private_router.message(Change_info.edit)
async def edit(message: Message, state: FSMContext):
    await state.update_data(edit = message.text.strip())
    await message.answer("Введи нове значення")
    await state.set_state(Change_info.value)


@admin_private_router.message(Change_info.value)
async def update_product_info(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    product_name = data.get("product_name")
    
    edit = data["edit"]
    value = message.text.strip()

    valid_fields = {
        "назва товару": '"Назва товару"',
        "ціна": '"Ціна"',
        "кількість": '"Кількість"',
    }

    if edit.lower() not in valid_fields:
        await message.answer("⚠️ Такого поля не існує. Використай: Назва товару / Ціна / Кількість.")
        await state.clear()
        return

    field_name = valid_fields[edit.lower()]

    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            UPDATE "{category}"
            SET {field_name} = ?
            WHERE "id" = ?
        """, (value, product_name))
        await db.commit()

    await message.answer(f"✅ Інформацію про товар <b>{product_name}</b> оновлено!", parse_mode="HTML")
    await state.clear()



@admin_private_router.message(F.text == "Закрити магазин")
async def close_shop(message: Message):
    await set_shop_status(True)
    await message.answer("✅ Магазин закрито.")

@admin_private_router.message(F.text == "Відкрити магазин")
async def open_shop(message: Message):
    await set_shop_status(False)
    await message.answer("✅ Магазин відкрито.")








