"""
PyMart Analytics — Зертханалық жұмыс №4 тесттері
Функционалдық үлгілер мен құрылымдар (Maybe, Either контейнерлері)

pytest іске қосу:
    py -m pytest tests/test_lab4.py -v
"""

from __future__ import annotations

import pytest

from app.core.models import Product
from app.core.lab4 import (
    Maybe,
    Either,
    safe_find_product_by_id,
    safe_calculate_discount_price,
    get_product_rating_description,
    process_product_pipeline,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def products() -> tuple[Product, ...]:
    return (
        Product(id=1, name="iPhone 15",     price=450_000, category_id=1, in_stock=True,  rating=4.8),
        Product(id=2, name="Samsung S24",   price=380_000, category_id=1, in_stock=True,  rating=4.5),
        Product(id=3, name="Xiaomi 13",     price=220_000, category_id=1, in_stock=False, rating=3.9),
        Product(id=4, name="Nike Air Max",  price=55_000,  category_id=2, in_stock=True,  rating=4.7),
    )


# ===========================================================================
# 1. MAYBE / OPTION КОНТЕЙНЕРІНІҢ ТЕСТТЕРі
# ===========================================================================

class TestMaybeContainer:
    def test_maybe_creation_valid(self):
        m = Maybe.of(10)
        assert not m.is_empty()
        assert m.get_or_else(0) == 10

    def test_maybe_creation_none(self):
        m = Maybe.of(None)
        assert m.is_empty()
        assert m.get_or_else(5) == 5

    def test_maybe_map_success(self):
        m = Maybe.of(5).map(lambda x: x * 2)
        assert not m.is_empty()
        assert m.get_or_else(0) == 10

    def test_maybe_map_empty(self):
        m = Maybe.of(None).map(lambda x: x * 2)
        assert m.is_empty()
        assert m.get_or_else(42) == 42

    def test_maybe_map_exception_handling(self):
        # Нөлге бөлу қатесі орын алғанда Maybe None (Nothing) қайтаруы тиіс
        m = Maybe.of(0).map(lambda x: 10 / x)
        assert m.is_empty()
        assert m.get_or_else(100) == 100

    def test_maybe_flat_map_success(self):
        m = Maybe.of(5).flat_map(lambda x: Maybe.of(x + 10))
        assert not m.is_empty()
        assert m.get_or_else(0) == 15

    def test_maybe_flat_map_returning_raw(self):
        m = Maybe.of(5).flat_map(lambda x: x * 3)
        assert not m.is_empty()
        assert m.get_or_else(0) == 15

    def test_maybe_flat_map_empty(self):
        m = Maybe.of(None).flat_map(lambda x: Maybe.of(x + 10))
        assert m.is_empty()

    def test_maybe_flat_map_exception(self):
        m = Maybe.of(5).flat_map(lambda x: 10 / 0)
        assert m.is_empty()

    def test_maybe_equality(self):
        assert Maybe.of(5) == Maybe.of(5)
        assert Maybe.of(None) == Maybe.of(None)
        assert Maybe.of(5) != Maybe.of(10)
        assert Maybe.of(5) != "NotAMaybe"

    def test_maybe_repr(self):
        assert repr(Maybe.of(5)) == "Just(5)"
        assert repr(Maybe.of(None)) == "Nothing"

    def test_maybe_chaining_transformations(self):
        pipeline = (
            Maybe.of("123")
            .map(int)
            .map(lambda x: x + 7)
            .map(str)
        )
        assert pipeline.get_or_else("0") == "130"

    def test_maybe_multiple_nones(self):
        m = Maybe.of(None).map(lambda x: x + 1).map(lambda x: x * 2)
        assert m.is_empty()

    def test_maybe_edge_case_booleans(self):
        m = Maybe.of(False).map(lambda x: not x)
        assert not m.is_empty()
        assert m.get_or_else(True) == True

    def test_maybe_edge_case_empty_string(self):
        m = Maybe.of("").map(len)
        assert not m.is_empty()
        assert m.get_or_else(-1) == 0


# ===========================================================================
# 2. EITHER КОНТЕЙНЕРІНІҢ ТЕСТТЕРі
# ===========================================================================

class TestEitherContainer:
    def test_either_right_creation(self):
        e = Either.right("success")
        assert e.is_right()
        assert not e.is_left()
        assert e.get_or_else("default") == "success"

    def test_either_left_creation(self):
        e = Either.left("error")
        assert not e.is_right()
        assert e.is_left()
        assert e.get_or_else("default") == "default"

    def test_either_map_success(self):
        e = Either.right(10).map(lambda x: x * 5)
        assert e.is_right()
        assert e.get_or_else(0) == 50

    def test_either_map_left(self):
        e = Either.left("fail").map(lambda x: x * 5)
        assert e.is_left()
        assert e.get_or_else(99) == 99

    def test_either_map_raises_exception(self):
        e = Either.right(0).map(lambda x: 5 / x)
        assert e.is_left()
        assert isinstance(e._value, ZeroDivisionError)

    def test_either_flat_map_success(self):
        e = Either.right(4).flat_map(lambda x: Either.right(x + 6))
        assert e.is_right()
        assert e.get_or_else(0) == 10

    def test_either_flat_map_returning_raw(self):
        e = Either.right(4).flat_map(lambda x: x * 2)
        assert e.is_right()
        assert e.get_or_else(0) == 8

    def test_either_flat_map_left(self):
        e = Either.left("init_error").flat_map(lambda x: Either.right(x + 1))
        assert e.is_left()
        assert e.get_or_else(0) == 0

    def test_either_flat_map_exception(self):
        e = Either.right(5).flat_map(lambda x: 1 / 0)
        assert e.is_left()

    def test_either_equality(self):
        assert Either.right(10) == Either.right(10)
        assert Either.left("err") == Either.left("err")
        assert Either.right(10) != Either.right(20)
        assert Either.right(10) != Either.left(10)
        assert Either.right(10) != "NotAnEither"

    def test_either_repr(self):
        assert repr(Either.right(123)) == "Right(123)"
        assert repr(Either.left("boom")) == "Left(boom)"

    def test_either_chaining_multiple_rights(self):
        res = (
            Either.right(2)
            .map(lambda x: x * 3)
            .map(lambda x: x + 4)
            .map(lambda x: x - 2)
        )
        assert res.get_or_else(0) == 8

    def test_either_left_propagation(self):
        res = (
            Either.right(10)
            .map(lambda x: x - 10)
            .map(lambda x: 50 / x)  # Нөлге бөлу қатесін тудырады (Left болады)
            .map(lambda x: x + 100) # Аттап өтіледі
        )
        assert res.is_left()


# ===========================================================================
# 3. ЖОБА ДЕРЕКТЕРІНІҢ ИНТЕГРАЦИЯЛЫҚ ТЕСТТЕРі
# ===========================================================================

class TestProjectContainersIntegration:
    def test_safe_find_product_existing(self, products):
        res = safe_find_product_by_id(products, 1)
        assert not res.is_empty()
        assert res.get_or_else(products[0]).name == "iPhone 15"

    def test_safe_find_product_missing(self, products):
        res = safe_find_product_by_id(products, 999)
        assert res.is_empty()

    def test_safe_calculate_discount_valid(self, products):
        res = safe_calculate_discount_price(products[0], 10.0)
        assert res.is_right()
        assert res.get_or_else(0.0) == 405_000.0

    def test_safe_calculate_discount_invalid_percent(self, products):
        res = safe_calculate_discount_price(products[0], 150.0)
        assert res.is_left()
        assert "пайызы" in str(res._value)

    def test_get_product_rating_description_high(self, products):
        desc = get_product_rating_description(products[0])
        assert not desc.is_empty()
        assert desc.get_or_else("") == "Өте жоғары баға"

    def test_get_product_rating_description_medium(self, products):
        desc = get_product_rating_description(products[2])
        assert not desc.is_empty()
        assert desc.get_or_else("") == "Орташа немесе төмен баға"

    def test_process_product_pipeline_found(self, products):
        name_upper = process_product_pipeline(products, 2)
        assert name_upper == "SAMSUNG S24"

    def test_process_product_pipeline_not_found(self, products):
        name_upper = process_product_pipeline(products, 999)
        assert name_upper == "БЕЛГІСІЗ ӨНІМ"

    def test_monad_interoperability_concept(self, products):
        # Maybe арқылы тауып, Either арқылы есептеулер тізбегін құру
        product_maybe = safe_find_product_by_id(products, 1)
        assert not product_maybe.is_empty()
        
        prod = product_maybe.get_or_else(products[1])
        either_res = safe_calculate_discount_price(prod, 20.0).map(lambda p: p / 1000)
        
        assert either_res.is_right()
        assert either_res.get_or_else(0.0) == 360.0