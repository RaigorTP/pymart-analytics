"""
PyMart Analytics — Cart Pure Functions
Зертханалық жұмыс №1: Себет логикасы — таза функциялар

Ереже: себет ешқашан тікелей өзгертілмейді.
Барлық операция жаңа CartItem / Order қайтарады.
"""

from __future__ import annotations

from functools import reduce

from app.core.models import CartItem, Discount, Order, Product


# ---------------------------------------------------------------------------
# Себет операциялары (таза функциялар)
# ---------------------------------------------------------------------------

def add_item(
    cart: tuple[CartItem, ...],
    product: Product,
    quantity: int = 1,
) -> tuple[CartItem, ...]:
    """
    Өнімді себетке қосады.
    Егер өнім бар болса — санын арттырады (жаңа кортеж).
    """
    for i, item in enumerate(cart):
        if item.product.id == product.id:
            updated = item._replace(quantity=item.quantity + quantity)
            return cart[:i] + (updated,) + cart[i + 1:]
    return cart + (CartItem(product=product, quantity=quantity),)


def remove_item(
    cart: tuple[CartItem, ...],
    product_id: int,
) -> tuple[CartItem, ...]:
    """Өнімді себеттен алып тастайды."""
    return tuple(filter(lambda item: item.product.id != product_id, cart))


def update_quantity(
    cart: tuple[CartItem, ...],
    product_id: int,
    new_quantity: int,
) -> tuple[CartItem, ...]:
    """Себеттегі өнім санын жаңартады."""
    if new_quantity <= 0:
        return remove_item(cart, product_id)
    return tuple(
        item._replace(quantity=new_quantity)
        if item.product.id == product_id
        else item
        for item in cart
    )


def cart_total(cart: tuple[CartItem, ...]) -> float:
    """Себет жиынтығын есептейді (reduce)."""
    return reduce(
        lambda acc, item: acc + item.product.price * item.quantity,
        cart,
        0.0,
    )


def cart_item_count(cart: tuple[CartItem, ...]) -> int:
    """Себеттегі өнімдер жалпы санын қайтарады."""
    return reduce(lambda acc, item: acc + item.quantity, cart, 0)


def apply_discount_to_cart(
    cart: tuple[CartItem, ...],
    discount: Discount,
) -> tuple[CartItem, ...]:
    """
    Жеңілдік кодын себетке қолданады.
    Минималды сома шартын тексереді — таза функция.
    """
    total = cart_total(cart)
    if total < discount.min_amount:
        return cart   # жеңілдік қолданылмайды, бастапқы себет қайтарылады

    return tuple(
        item._replace(
            product=item.product._replace(
                price=round(item.product.price * (1 - discount.percent / 100), 2)
            )
        )
        for item in cart
    )


def checkout(
    order_id: int,
    customer_name: str,
    cart: tuple[CartItem, ...],
) -> Order:
    """
    Себеттен тапсырыс жасайды.
    Тапсырыс frozen dataclass — өзгерту мүмкін емес.
    """
    if not cart:
        raise ValueError("Себет бос — тапсырыс жасау мүмкін емес.")
    return Order(
        id=order_id,
        customer_name=customer_name,
        items=cart,
    )
