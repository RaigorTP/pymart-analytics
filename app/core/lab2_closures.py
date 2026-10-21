"""
PyMart Analytics — Зертханалық жұмыс №2
Lambda функциялары + Жабылулар (Closures) + Рекурсия

Лекция 5: Lambda, Closures
Лекция 6: Recursion
"""

from __future__ import annotations

from functools import lru_cache
from typing import Callable

from app.core.models import Product, CartItem, Order

# ===========================================================================
# БӨЛІМ 1: LAMBDA ФУНКЦИЯЛАРЫ
# ===========================================================================

# --- Негізгі lambda мысалдары ---

# Қарапайым lambda
square      = lambda x: x ** 2
add         = lambda x, y: x + y
is_even     = lambda n: n % 2 == 0

# Lambda + map: бағаларды форматтау
def format_prices(products: tuple[Product, ...]) -> tuple[str, ...]:
    """map + lambda: баға → 'iPhone 15: 450 000 ₸' форматы."""
    return tuple(
        map(lambda p: f"{p.name}: {p.price:,.0f} ₸", products)
    )

# Lambda + filter: рейтинг бойынша сүзу
def top_rated(
    products: tuple[Product, ...],
    threshold: float = 4.5,
) -> tuple[Product, ...]:
    """filter + lambda: жоғары рейтингті өнімдер."""
    return tuple(filter(lambda p: p.rating >= threshold, products))

# Lambda + sorted: күрделі сұрыптау кілті
def sort_by_value_score(
    products: tuple[Product, ...],
) -> tuple[Product, ...]:
    """
    Баға / рейтинг қатынасы бойынша сұрыптау.
    Lambda күрделі кілт ретінде.
    """
    return tuple(
        sorted(products, key=lambda p: p.price / max(p.rating, 0.1))
    )


# ===========================================================================
# БӨЛІМ 2: ЖАБЫЛУЛАР (CLOSURES) — конфигуратор-фабрикалар
# ===========================================================================

def make_category_filter(
    category_id: int,
) -> Callable[[Product], bool]:
    """
    Жабылу-конфигуратор: категория бойынша предикат жасайды.

    Closure: ішкі функция сыртқы category_id айнымалысын «жабады».

    Мысал:
        phones_only = make_category_filter(1)
        phones_only(product)  → True/False
    """
    def predicate(product: Product) -> bool:
        return product.category_id == category_id
    return predicate


def make_price_filter(
    min_price: float = 0.0,
    max_price: float = float("inf"),
) -> Callable[[Product], bool]:
    """
    Жабылу: баға диапазоны бойынша сүзгі жасайды.
    min_price және max_price ішкі функцияда «жабылады».
    """
    def predicate(product: Product) -> bool:
        return min_price <= product.price <= max_price
    return predicate


def make_rating_filter(
    min_rating: float,
) -> Callable[[Product], bool]:
    """Жабылу: минималды рейтинг бойынша сүзгі."""
    def predicate(product: Product) -> bool:
        return product.rating >= min_rating
    return predicate


def make_stock_filter(in_stock: bool = True) -> Callable[[Product], bool]:
    """Жабылу: қоймада бар/жоқ бойынша сүзгі."""
    def predicate(product: Product) -> bool:
        return product.in_stock == in_stock
    return predicate


def make_combined_filter(
    *predicates: Callable[[Product], bool],
) -> Callable[[Product], bool]:
    """
    Жабылу-комбинатор: бірнеше предикатты AND логикасымен біріктіреді.
    predicates тізімі ішкі функцияда жабылады.

    Мысал:
        f = make_combined_filter(
                make_category_filter(1),
                make_price_filter(max_price=400_000),
                make_rating_filter(4.5),
            )
        filtered = tuple(filter(f, products))
    """
    def combined(product: Product) -> bool:
        return all(pred(product) for pred in predicates)
    return combined


def make_discount_applier(percent: float) -> Callable[[Product], Product]:
    """
    Жабылу-трансформатор: берілген пайызбен жеңілдік қолданады.
    percent мәні ішкі функцияда сақталады.
    """
    def apply(product: Product) -> Product:
        new_price = round(product.price * (1 - percent / 100), 2)
        return product._replace(price=new_price)
    return apply


def make_price_multiplier(factor: float) -> Callable[[float], float]:
    """
    Жабылу: бағаны берілген коэффициентке көбейтеді.
    factor ішкі функцияда «жабылады» — классикалық closure мысалы.
    """
    def multiply(price: float) -> float:
        return round(price * factor, 2)
    return multiply


def make_order_status_filter(
    status: str,
) -> Callable[[Order], bool]:
    """Жабылу: тапсырыс статусы бойынша предикат."""
    def predicate(order: Order) -> bool:
        return order.status == status
    return predicate


# ===========================================================================
# БӨЛІМ 3: РЕКУРСИЯ
# ===========================================================================

# ---------------------------------------------------------------------------
# Рекурсивті алгоритм №1: Категория ағашында іздеу
# ---------------------------------------------------------------------------

# Категория ағашы: {id: {"name": str, "children": [...]}}
CategoryTree = dict[str, object]


def find_category_in_tree(
    tree: list[CategoryTree],
    target_id: int,
) -> CategoryTree | None:
    """
    Рекурсивті іздеу: категория ағашынан id бойынша табу.

    Негізгі жағдай (base case): ағаш бос → None
    Рекурсивті жағдай: ішкі "children" тізімінде іздеуді жалғастыру.

    Мысал ағашы:
        [
            {"id": 1, "name": "Электроника", "children": [
                {"id": 11, "name": "Телефондар", "children": []},
                {"id": 12, "name": "Ноутбуктер", "children": []},
            ]},
            {"id": 2, "name": "Спорт", "children": []},
        ]
    """
    for node in tree:
        if node["id"] == target_id:
            return node
        # Рекурсия: ішкі категорияларда іздеу
        children = node.get("children", [])
        result = find_category_in_tree(children, target_id)
        if result is not None:
            return result
    return None


def collect_all_category_ids(
    tree: list[CategoryTree],
) -> list[int]:
    """
    Рекурсия: ағаштан барлық категория id-ларін жинайды.
    Base case: ағаш бос → []
    """
    if not tree:
        return []
    ids = []
    for node in tree:
        ids.append(node["id"])
        ids.extend(collect_all_category_ids(node.get("children", [])))
    return ids


def tree_depth(tree: list[CategoryTree]) -> int:
    """
    Рекурсия: ағаш тереңдігін есептейді.
    Base case: бос ағаш → 0
    """
    if not tree:
        return 0
    return 1 + max(
        (tree_depth(node.get("children", [])) for node in tree),
        default=0,
    )


# ---------------------------------------------------------------------------
# Рекурсивті алгоритм №2: Тапсырыстар агрегациясы
# ---------------------------------------------------------------------------

def recursive_total(items: list[float], index: int = 0) -> float:
    """
    Рекурсивті сома есептеу (reduce баламасы).
    Base case: index >= len(items) → 0
    Recursive case: items[index] + recursive_total(items, index + 1)
    """
    if index >= len(items):
        return 0.0
    return items[index] + recursive_total(items, index + 1)


def recursive_max(items: list[float], index: int = 0) -> float:
    """
    Рекурсивті максимум іздеу.
    Base case: тізімде 1 элемент → сол элемент
    """
    if index == len(items) - 1:
        return items[index]
    rest_max = recursive_max(items, index + 1)
    return items[index] if items[index] > rest_max else rest_max


def flatten_cart_items(
    nested: list,
) -> list[CartItem]:
    """
    Рекурсия: кіріктірілген тізімдегі CartItem-ларды жалпақтандырады.
    Base case: бос тізім → []
    Рекурсивті жағдай: ішкі тізімдерге кіру.

    Мысал: [[item1, item2], [item3, [item4]]] → [item1, item2, item3, item4]
    """
    result = []
    for element in nested:
        if isinstance(element, list):
            result.extend(flatten_cart_items(element))
        else:
            result.append(element)
    return result


@lru_cache(maxsize=None)
def fibonacci(n: int) -> int:
    """
    Рекурсивті Фибоначчи + мемоизация (lru_cache).
    Base case: n <= 1 → n
    """
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@lru_cache(maxsize=None)
def factorial(n: int) -> int:
    """
    Рекурсивті факторлық + мемоизация.
    Base case: n == 0 → 1
    """
    if n == 0:
        return 1
    return n * factorial(n - 1)


# ---------------------------------------------------------------------------
# Рекурсивті алгоритм №3: Іріктелген өнімдер есебі (ағаш агрегациясы)
# ---------------------------------------------------------------------------

def aggregate_revenue_by_tree(
    tree: list[CategoryTree],
    products: tuple[Product, ...],
    orders_by_product: dict[int, float],
) -> dict[int, float]:
    """
    Рекурсия: категория ағашы бойынша табысты агрегаттайды.
    Ішкі категориялардың табысы жоғарыға «көтеріледі».

    Base case: children жоқ → тек осы категориядағы өнімдер
    Recursive case: children табысын қосу
    """
    result: dict[int, float] = {}

    for node in tree:
        cat_id = node["id"]
        # Тікелей осы категориядағы өнімдер табысы
        direct_revenue = sum(
            orders_by_product.get(p.id, 0.0)
            for p in products
            if p.category_id == cat_id
        )
        # Рекурсия: ішкі категориялар табысы
        children_revenue = aggregate_revenue_by_tree(
            node.get("children", []), products, orders_by_product
        )
        subtotal = direct_revenue + sum(children_revenue.values())
        result[cat_id] = subtotal
        result.update(children_revenue)

    return result
