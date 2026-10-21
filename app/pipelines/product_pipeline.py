"""
PyMart Analytics — Pipeline демонстрациясы
Зертханалық жұмыс №1: map / filter / reduce конвейерлер

Лекция 4 бойынша: HOF тізбегі — функциялық конвейер (pipeline).
"""

from __future__ import annotations

from functools import reduce
from typing import Callable, TypeVar

from app.core.models import Product

T = TypeVar("T")
U = TypeVar("U")


# ---------------------------------------------------------------------------
# Жалпы pipeline утилиталары
# ---------------------------------------------------------------------------

def pipe(*fns: Callable) -> Callable:
    """
    Функцияларды тізбектейді: pipe(f, g, h)(x) = h(g(f(x)))
    HOF + reduce комбинациясы.
    """
    return reduce(lambda f, g: lambda x: g(f(x)), fns)


def compose(*fns: Callable) -> Callable:
    """
    Кері тәртіппен тізбектейді: compose(f, g)(x) = f(g(x))
    Математикалық функция композициясы.
    """
    return reduce(lambda f, g: lambda x: f(g(x)), fns)


# ---------------------------------------------------------------------------
# Өнім конвейерлері (нақты мысалдар)
# ---------------------------------------------------------------------------

def catalog_pipeline(
    products: tuple[Product, ...],
    category_id: int | None = None,
    min_rating: float = 0.0,
    max_price: float | None = None,
    sort_by_price: bool = True,
) -> tuple[Product, ...]:
    """
    Каталог конвейері — шарттар тізбегі.

    Байқап отырыңыз: әрбір қадам жаңа tuple қайтарады,
    бастапқы деректер өзгертілмейді (иммутабельділік).
    """
    result = products

    # 1) тек қоймада барлар
    result = tuple(filter(lambda p: p.in_stock, result))

    # 2) категория бойынша (егер берілсе)
    if category_id is not None:
        result = tuple(filter(lambda p: p.category_id == category_id, result))

    # 3) минималды рейтинг
    result = tuple(filter(lambda p: p.rating >= min_rating, result))

    # 4) максималды баға
    if max_price is not None:
        result = tuple(filter(lambda p: p.price <= max_price, result))

    # 5) сұрыптау
    if sort_by_price:
        result = tuple(sorted(result, key=lambda p: p.price))

    return result


def discount_pipeline(
    products: tuple[Product, ...],
    discounts: tuple[tuple[int, float], ...],
) -> tuple[Product, ...]:
    """
    Категорияға сай жеңілдік қолданатын конвейер.
    discounts = ((category_id, percent), ...)

    map + dict іздеу = таза трансформация.
    """
    discount_map = dict(discounts)
    return tuple(
        map(
            lambda p: p._replace(
                price=round(p.price * (1 - discount_map[p.category_id] / 100), 2)
            )
            if p.category_id in discount_map
            else p,
            products,
        )
    )


def summary_pipeline(products: tuple[Product, ...]) -> dict:
    """
    Каталог жиынтығын есептейтін конвейер.
    reduce арқылы бір өтумен барлық статистика.
    """
    if not products:
        return {"count": 0, "total": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}

    prices = tuple(map(lambda p: p.price, products))

    total = reduce(lambda a, b: a + b, prices, 0.0)
    return {
        "count": len(products),
        "total": round(total, 2),
        "avg": round(total / len(products), 2),
        "min": min(prices),
        "max": max(prices),
    }
