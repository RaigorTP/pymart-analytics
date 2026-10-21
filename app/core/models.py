"""
PyMart Analytics — Domain Models
Зертханалық жұмыс №1: Өзгермейтін деректер құрылымдары (NamedTuple / frozen dataclass)

Лекция 1-3 бойынша:
  - Деректердің өзгермейтіндігі (immutability)
  - Таза функциялар (pure functions)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


# ---------------------------------------------------------------------------
# 1. NamedTuple — кортеж негізіндегі өзгермейтін мән
# ---------------------------------------------------------------------------

class Category(NamedTuple):
    """Өнім категориясы — толығымен өзгермейтін (NamedTuple)."""
    id: int
    name: str
    description: str = ""


class Product(NamedTuple):
    """
    Өнім — домейндік мән-нысан.
    NamedTuple өзгертуге болмайды: p.price = 5  → AttributeError
    """
    id: int
    name: str
    price: float          # теңге (KZT)
    category_id: int
    in_stock: bool = True
    rating: float = 0.0   # 0.0 – 5.0


class CartItem(NamedTuple):
    """Себет жолы — өнім + саны."""
    product: Product
    quantity: int


# ---------------------------------------------------------------------------
# 2. frozen dataclass — аты бар өрістер + қателерден қорғаныш
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Order:
    """
    Тапсырыс — frozen=True болғандықтан өзгертуге болмайды.
    Жаңа күй үшін → dataclasses.replace(order, status="shipped") қолданылады.
    """
    id: int
    customer_name: str
    items: tuple[CartItem, ...]   # list емес tuple — өзгермейтін
    status: str = "pending"       # pending | paid | shipped | cancelled

    @property
    def total(self) -> float:
        """Тапсырыс жиынтығы — жанама әсерсіз есептеу."""
        return sum(item.product.price * item.quantity for item in self.items)


@dataclass(frozen=True)
class Discount:
    """Жеңілдік ережесі."""
    code: str
    percent: float    # 0.0 – 100.0
    min_amount: float = 0.0
