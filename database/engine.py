import aiosqlite, asyncio
import re
import aiogram
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from bot_main import DB_PATH
import datetime


async def test_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)"
        )
        await db.commit()
        print("✅ Database connected successfully!")


asyncio.run(test_db())


async def list_db():
    """Повертає всі товари по категоріях (таблицях) з індексом"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Отримуємо список таблиць (виключаємо системні таблиці)
        async with db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
        """) as cursor:
            tables = await cursor.fetchall()

        all_products = {}
        for table in tables:
            table_name = table[0]

            # Додаємо rowid як окрему колонку з іменем
            async with db.execute(
                f"SELECT rowid as id, * FROM '{table_name}'") as cursor2:
                rows = await cursor2.fetchall()
                products = []
                for row in rows:
                    try:
                        # Отримуємо id (rowid)
                        row_id = row["id"]
                        # Перевіряємо наявність ключів
                        name = row[
                            "Назва товару"] if "Назва товару" in row.keys(
                            ) else "Немає назви"
                        price = row["Ціна"] if "Ціна" in row.keys() else "0"
                        products.append((row_id, name, price))
                    except (KeyError, IndexError) as e:
                        print(
                            f"Помилка при обробці рядка в таблиці {table_name}: {e}"
                        )
                        continue

                if products:
                    all_products[table_name] = products

        return all_products


async def show_something(category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute(
                    f'SELECT rowid as id, * FROM "{category}"') as cursor:
                rows = await cursor.fetchall()
        except aiosqlite.OperationalError as e:
            print(f"Таблиці для категорії '{category}' не існує: {e}")
            return []

        if not rows:
            return []

        products = []
        for row in rows:
            try:
                row_id = row["id"]
                name = row["Назва товару"] if "Назва товару" in row.keys(
                ) else "Немає назви"
                price = row["Ціна"] if "Ціна" in row.keys() else "0"
                photo = row["photo_id"] if "photo_id" in row.keys(
                ) else "Немає фото"
                quantity = row["Кількість"] if "Кількість" in row.keys(
                ) else "0"
                products.append((row_id, name, price, photo, quantity))
            except (KeyError, IndexError) as e:
                print(f"Помилка при обробці рядка в таблиці {category}: {e}")
                continue

        return products


async def delete(category: str, id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        response = await show_something(category=category)

        selected = next((p for p in response if p[0] == id), None)

        if not selected:
            print(f"❌ Товар із ID {id} не знайдено у категорії {category}.")
            return

        row_id, name, price, photo, quantity = selected
        await db.execute(f"DELETE FROM '{category}' WHERE rowid = ?", (id, ))
        await db.commit()
        print(f"✅ Товар {name} видалено успішно.")
        update = await show_something(category)
        return update


async def add_something(category, data):
    async with aiosqlite.connect(DB_PATH) as db:
        name = data["name"]
        price = data["price"]
        image = data["image"]
        quantity = data["quantity"]

        await db.execute(
            f"INSERT INTO '{category}' ('Назва товару', 'Ціна', 'photo_id', 'Кількість') VALUES (?, ?, ?, ?)",
            (name, price, image, quantity)  # ✅ Додай параметри!
        )
        await db.commit()  # ✅ Додай дужки!


async def add_photo(data, image):
    async with aiosqlite.connect(DB_PATH) as db:
        category = data["product_category"]
        image = data["product_photo"]
        id = data["product_id"]

        await db.execute(f"UPDATE '{category}' SET photo_id = ? WHERE id = ?",
                         (image, id))

        await db.commit()


async def buy(category: str, id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        response = await show_something(category=category)

        selected = next((p for p in response if p[0] == id), None)

        if not selected:
            print(f"❌ Товар із ID {id} не знайдено у категорії {category}.")
            return
        row_id, name, price, photo, quantity = selected

        if quantity > 1:
            await db.execute(
                f"UPDATE '{category}' SET 'Кількість'= ? WHERE id = ?",
                (quantity - 1, id))

        else:
            await db.execute(f"DELETE FROM '{category}' WHERE rowid = ?",
                             (id, ))

        await db.commit()
        print(
            f"✅ Оновлено товар {name}: нова кількість {max(quantity - 1, 0)}")


async def create_category(category: str):
    # 1️⃣ Прибираємо зайві пробіли з країв
    category = category.strip()

    # 2️⃣ Прибираємо тільки небезпечні спецсимволи, але ЗАЛИШАЄМО пробіли
    category = re.sub(r'[^\w\s]', '', category, flags=re.UNICODE)
    #                                      ❗️ Додав пробіл у дозволені символи

    # 3️⃣ Заміняємо множинні пробіли на один
    category = re.sub(r'\s+', ' ', category)

    # 4️⃣ Якщо після фільтрації залишилося пусто
    if not category:
        raise ValueError("Некоректна назва категорії!")

    # 5️⃣ Перевіряємо зарезервовані SQL-слова
    forbidden = {
        "select", "from", "table", "insert", "delete", "update", "where",
        "join", "drop", "create"
    }
    if category.lower() in forbidden:
        raise ValueError(
            f"'{category}' — це зарезервоване слово SQL, обери іншу назву!")

    # 6️⃣ Створюємо таблицю
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f'''
            CREATE TABLE IF NOT EXISTS "{category}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                "Назва товару" TEXT NOT NULL,
                "Ціна" REAL NOT NULL,
                "photo_id" TEXT,
                "Кількість" INTEGER DEFAULT 1
            )
        ''')
        await db.commit()


async def delete_category(category: str):
    async with aiosqlite.connect(DB_PATH) as db:

        # Перевіряємо чи існує таблиця
        cursor = await db.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (category, ))

        exists = await cursor.fetchone()

        if not exists:
            raise ValueError(f"Категорія '{category}' не існує!")

        # Видаляємо таблицю
        await db.execute(f'DROP TABLE IF EXISTS "{category}"')
        await db.commit()


async def update_info(data):
    async with aiosqlite.connect(DB_PATH) as db:
        category = data["category"]
        product_name = data["product_name"]
        edit = data["edit"]
        value = data["value"]

        await db.execute(
            f"""UPDATE "{category}"
                         SET {edit} = ?
                         WHERE "Назва товару" = ?
                         """, (value, product_name))
        await db.commit()


async def get_all_categories():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type = 'table' 
            AND name NOT LIKE 'sqlite_%'
        """)
        rows = await cursor.fetchall()

        # Виключаємо службові/зайві таблиці
        exclude = []
        categories = [row[0] for row in rows if row[0] not in exclude]

        print(f"✅ Знайдено категорії: {categories}")  # Для перевірки
        return categories



import aiosqlite
from bot_main import DB_PATH  # твій шлях до бази

# ------------------------
# Створення таблиці (на старті)
# ------------------------
async def init_shop_status_table():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS shop_status")  # для тестів
        await db.execute("""
            CREATE TABLE shop_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                is_closed BOOLEAN NOT NULL
            )
        """)
        await db.commit()
    print("✅ Таблиця shop_status створена заново")


# ------------------------
# Закрити / Відкрити магазин
# ------------------------
async def set_shop_status(closed: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        # залишаємо тільки останній запис
        await db.execute("DELETE FROM shop_status")
        await db.execute(
            "INSERT INTO shop_status (is_closed) VALUES (?)",
            (int(closed),)
        )
        await db.commit()


# ------------------------
# Перевірка статусу магазину
# ------------------------
async def is_shop_closed() -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT is_closed FROM shop_status ORDER BY id DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return bool(row["is_closed"])
    return False





