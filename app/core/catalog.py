"""
PyMart Analytics — Catalog Pure Functions
Зертханалық жұмыс №1: Таза функциялар (Pure Functions)

Лекция 3 бойынша:
  - Таза функция = бірдей кіріс → бірдей шығыс + жанама әсер жоқ
  - Сыртқы күйді өзгертпейді
"""

from __future__ import annotations

from functools import reduce
from typing import Callable

from app.core.models import Product


# ---------------------------------------------------------------------------
# Таза трансформация функциялары
# ---------------------------------------------------------------------------

def apply_discount(product: Product, percent: float) -> Product:
    """
    Жеңілдік қолданылған жаңа Product қайтарады.
    Бастапқы product өзгертілмейді — жаңа экземпляр жасалады.
    """
    new_price = round(product.price * (1 - percent / 100), 2)
    return product._replace(price=new_price)


def mark_out_of_stock(product: Product) -> Product:
    """Өнімді қоймада жоқ деп белгілейді (жаңа нысан)."""
    return product._replace(in_stock=False)


def update_rating(product: Product, new_rating: float) -> Product:
    """Бағалауды жаңартқан жаңа Product қайтарады."""
    if not (0.0 <= new_rating <= 5.0):
        raise ValueError(f"Рейтинг 0–5 аралығында болуы керек, берілген: {new_rating}")
    return product._replace(rating=round(new_rating, 1))


# ---------------------------------------------------------------------------
# HOF (Higher-Order Functions) — map / filter / reduce конвейерлер
# ---------------------------------------------------------------------------

def filter_by_category(
    products: tuple[Product, ...],
    category_id: int,
) -> tuple[Product, ...]:
    """
    Берілген категориядағы өнімдерді сүзеді.
    HOF: filter() ішкі функционалдық конвейер.
    """
    return tuple(filter(lambda p: p.category_id == category_id, products))


def filter_in_stock(products: tuple[Product, ...]) -> tuple[Product, ...]:
    """Тек қоймада бар өнімдерді қалдырады."""
    return tuple(filter(lambda p: p.in_stock, products))


def filter_by_min_rating(
    products: tuple[Product, ...],
    min_rating: float,
) -> tuple[Product, ...]:
    """Минималды рейтингтен жоғары өнімдерді қайтарады."""
    return tuple(filter(lambda p: p.rating >= min_rating, products))


def apply_discount_to_all(
    products: tuple[Product, ...],
    percent: float,
) -> tuple[Product, ...]:
    """
    Барлық өнімге жеңілдік қолданады.
    HOF: map() арқылы трансформация.
    """
    return tuple(map(lambda p: apply_discount(p, percent), products))


def get_names(products: tuple[Product, ...]) -> tuple[str, ...]:
    """Өнімдер атауларының тізімін шығарады (map мысалы)."""
    return tuple(map(lambda p: p.name, products))


def total_catalog_value(products: tuple[Product, ...]) -> float:
    """
    Барлық өнімдердің жалпы құны (reduce мысалы).
    reduce(f, [a, b, c]) = f(f(a, b), c)
    """
    if not products:
        return 0.0
    return reduce(lambda acc, p: acc + p.price, products, 0.0)


def average_price(products: tuple[Product, ...]) -> float:
    """Орташа баға — таза функция (reduce + len)."""
    if not products:
        return 0.0
    return total_catalog_value(products) / len(products)


def sort_by(
    products: tuple[Product, ...],
    key_fn: Callable[[Product], float | str | int],
    reverse: bool = False,
) -> tuple[Product, ...]:
    """
    HOF: кілт функциясымен сұрыптау.
    Мысал: sort_by(products, lambda p: p.price)
    """
    return tuple(sorted(products, key=key_fn, reverse=reverse))


def search_by_name(
    products: tuple[Product, ...],
    query: str,
) -> tuple[Product, ...]:
    """Атауы бойынша іздеу (регистрге тәуелсіз)."""
    q = query.lower()
    return tuple(filter(lambda p: q in p.name.lower(), products))
