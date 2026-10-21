"""
PyMart Analytics — Reports Pure Functions
Зертханалық жұмыс №1: Аналитикалық есептер — map/filter/reduce конвейерлер
"""

from __future__ import annotations

from collections import Counter
from functools import reduce
from typing import TypedDict

from app.core.models import Order, Product


# ---------------------------------------------------------------------------
# Есеп типтері (TypedDict — оқуға ыңғайлы, типтелген)
# ---------------------------------------------------------------------------

class SalesReport(TypedDict):
    total_orders: int
    total_revenue: float
    average_order_value: float
    top_product_id: int | None


class CategoryReport(TypedDict):
    category_id: int
    product_count: int
    avg_price: float
    min_price: float
    max_price: float


# ---------------------------------------------------------------------------
# Таза аналитика функциялары
# ---------------------------------------------------------------------------

def total_revenue(orders: tuple[Order, ...]) -> float:
    """Барлық тапсырыстардың жалпы табысы (reduce)."""
    return reduce(lambda acc, o: acc + o.total, orders, 0.0)


def paid_orders(orders: tuple[Order, ...]) -> tuple[Order, ...]:
    """Тек төленген тапсырыстарды сүзеді (filter)."""
    return tuple(filter(lambda o: o.status == "paid", orders))


def average_order_value(orders: tuple[Order, ...]) -> float:
    """Орташа тапсырыс сомасы."""
    if not orders:
        return 0.0
    return total_revenue(orders) / len(orders)


def top_selling_product_id(orders: tuple[Order, ...]) -> int | None:
    """
    Ең көп сатылған өнімнің id-ін табады.
    map + reduce арқылы: тапсырыстардан → Counter → max
    """
    if not orders:
        return None

    # Барлық items-тарды жалпақтандыру (flatten) — map + reduce
    all_items = reduce(
        lambda acc, o: acc + list(o.items),
        orders,
        [],
    )

    # Өнім id → жалпы саны
    counts: Counter[int] = Counter(
        reduce(
            lambda acc, item: acc + [item.product.id] * item.quantity,
            all_items,
            [],
        )
    )

    return counts.most_common(1)[0][0] if counts else None


def build_sales_report(orders: tuple[Order, ...]) -> SalesReport:
    """Сатылым есебін жасайды — таза функция."""
    paid = paid_orders(orders)
    return SalesReport(
        total_orders=len(paid),
        total_revenue=total_revenue(paid),
        average_order_value=average_order_value(paid),
        top_product_id=top_selling_product_id(paid),
    )


def category_report(
    products: tuple[Product, ...],
    category_id: int,
) -> CategoryReport:
    """Категория бойынша есеп — filter + map + reduce."""
    cat_products = tuple(
        filter(lambda p: p.category_id == category_id, products)
    )
    if not cat_products:
        return CategoryReport(
            category_id=category_id,
            product_count=0,
            avg_price=0.0,
            min_price=0.0,
            max_price=0.0,
        )

    prices = tuple(map(lambda p: p.price, cat_products))
    return CategoryReport(
        category_id=category_id,
        product_count=len(cat_products),
        avg_price=round(reduce(lambda a, b: a + b, prices) / len(prices), 2),
        min_price=min(prices),
        max_price=max(prices),
    )


def revenue_by_category(
    orders: tuple[Order, ...],
) -> dict[int, float]:
    """
    Категория бойынша табыс картасы.
    map → reduce конвейері.
    """
    result: dict[int, float] = {}
    for order in paid_orders(orders):
        for item in order.items:
            cat_id = item.product.category_id
            result[cat_id] = result.get(cat_id, 0.0) + (
                item.product.price * item.quantity
            )
    return result
