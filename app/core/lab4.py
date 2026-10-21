"""
PyMart Analytics — Зертханалық жұмыс №4
Функционалдық үлгілер мен құрылымдар (Option/Maybe, Either монадалары)

Лекция 8 бойынша:
  - Қателерді және бос мәндерді қауіпсіз өңдеу (Option/Maybe, Either)
  - Монадикалық контейнерлер мен трансформациялар композициясы
  - Функционалдық дизайн үлгілері
"""

from __future__ import annotations

from typing import Callable, TypeVar, Generic, Any
from app.core.models import Product

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


# ===========================================================================
# БӨЛІМ 1: MAYBE (OPTION) КОНТЕЙНЕРІ — БОС МӘНДЕРДІ ҚАУІПСІЗ ӨҢДЕУ
# ===========================================================================

class Maybe(Generic[T]):
    """
    Қателерді/бос мәндерді (None) қауіпсіз өңдеуге арналған Option/Maybe контейнері.
    Функционалдық бағдарламалаудағы Null pointer ерекшеліктерін болдырмайды.
    """
    
    def __init__(self, value: T | None):
        self._value = value

    @staticmethod
    def of(value: T | None) -> Maybe[T]:
        """Мәні бар немесе жоқ (None) Maybe контейнерін құру."""
        return Maybe(value)

    def is_empty(self) -> bool:
        """Контейнердің бос екенін тексеру."""
        return self._value is None

    def map(self, func: Callable[[T], U]) -> Maybe[U]:
        """
        Егер мән бар болса, берілген функцияны қолданып, 
        нәтижені жаңа Maybe контейнеріне орайды.
        """
        if self.is_empty():
            return Maybe(None)
        try:
            result = func(self._value)  # type: ignore[arg-type]
            return Maybe(result)
        except Exception:
            return Maybe(None)

    def flat_map(self, func: Callable[[T], Maybe[U]]) -> Maybe[U]:
        """
        Монадикалық bind (flat_map): нәтижесі өзі Maybe болатын функцияны 
        қолданғанда Maybe(Maybe(val)) болып қабаттасып кетуден сақтайды.
        """
        if self.is_empty():
            return Maybe(None)
        try:
            result = func(self._value)  # type: ignore[arg-type]
            if isinstance(result, Maybe):
                return result
            return Maybe(result)
        except Exception:
            return Maybe(None)

    def get_or_else(self, default: T) -> T:
        """Контейнер бос болса әдепкі мәнді, керісінше ішкі мәнді қайтарады."""
        return self._value if not self.is_empty() else default

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Maybe):
            return False
        return self._value == other._value

    def __repr__(self) -> str:
        return f"Just({self._value})" if not self.is_empty() else "Nothing"


# ===========================================================================
# БӨЛІМ 2: EITHER КОНТЕЙНЕРІ — СӘТТІ НӘТИЖЕ ЖӘНЕ ҚАТЕТІ ӨҢДЕУ
# ===========================================================================

class Either(Generic[E, T]):
    """
    Сәтті нәтижені (Right) немесе қате туралы ақпаратты (Left) сақтауға арналған контейнер.
    """
    
    def __init__(self, value: Any, is_right: bool = True):
        self._value = value
        self._is_right = is_right

    @staticmethod
    def right(value: T) -> Either[Any, T]:
        """Сәтті нәтижені жасау (Right)."""
        return Either(value, is_right=True)

    @staticmethod
    def left(value: E) -> Either[E, Any]:
        """Қатені немесе ерекше жағдайды жасау (Left)."""
        return Either(value, is_right=False)

    def is_right(self) -> bool:
        return self._is_right

    def is_left(self) -> bool:
        return not self._is_right

    def map(self, func: Callable[[T], U]) -> Either[E, U]:
        """Тек Right (сәтті) жағдайында ғана функцияны қолданады."""
        if self.is_left():
            return self  # type: ignore[return-value]
        try:
            return Either.right(func(self._value))
        except Exception as e:
            return Either.left(e)  # type: ignore[return-value]

    def flat_map(self, func: Callable[[T], Either[E, U]]) -> Either[E, U]:
        """Either үшін монадикалық bind (flat_map)."""
        if self.is_left():
            return self  # type: ignore[return-value]
        try:
            result = func(self._value)
            if isinstance(result, Either):
                return result
            return Either.right(result)
        except Exception as e:
            return Either.left(e)  # type: ignore[return-value]

    def get_or_else(self, default: T) -> T:
        return self._value if self.is_right() else default  # type: ignore[return-value]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Either):
            return False
        return self._value == other._value and self._is_right == other._is_right

    def __repr__(self) -> str:
        return f"Right({self._value})" if self.is_right() else f"Left({self._value})"


# ===========================================================================
# БӨЛІМ 3: ЖОБАНЫҢ НАҚТЫ ДЕРЕКТЕРІНЕ КОНТЕЙНЕРЛЕРДІ ҚОЛДАНУ
# ===========================================================================

def safe_find_product_by_id(products: tuple[Product, ...], product_id: int) -> Maybe[Product]:
    """
    Өнімді ID арқылы қауіпсіз іздеу (Maybe қайтарады).
    Егер табылмаса Nothing қайтарады.
    """
    found = next((p for p in products if p.id == product_id), None)
    return Maybe.of(found)


def safe_calculate_discount_price(product: Product, discount_percent: float) -> Either[str, float]:
    """
    Жеңілдік бағасын қауіпсіз есептеу (Either қайтарады).
    Параметрлер қате болса Left түрінде қате хабарламасын береді.
    """
    if discount_percent < 0 or discount_percent > 100:
        return Either.left("Қате: Жеңілдік пайызы 0 мен 100 арасында болуы тиіс")
    if product.price < 0:
        return Either.left("Қате: Өнім бағасы теріс болмауы керек")
    
    final_price = product.price * (1 - discount_percent / 100)
    return Either.right(final_price)


def get_product_rating_description(product: Product) -> Maybe[str]:
    """
    Өнім рейтингі негізінде сипаттама беру (Maybe арқылы трансформация).
    """
    if product.rating is None:
        return Maybe.of(None)
    
    if product.rating >= 4.5:
        return Maybe.of("Өте жоғары баға")
    elif product.rating >= 4.0:
        return Maybe.of("Жақсы баға")
    else:
        return Maybe.of("Орташа немесе төмен баға")


def process_product_pipeline(products: tuple[Product, ...], target_id: int) -> str:
    """
    Трансформация композициясын көрсету:
    Maybe арқылы өнімді тауып, оның атауын бас әріптерге айналдыру 
    немесе әдепкі мән қайтару.
    """
    return (
        safe_find_product_by_id(products, target_id)
        .map(lambda p: p.name)
        .map(lambda name: name.upper())
        .get_or_else("БЕЛГІСІЗ ӨНІМ")
    )