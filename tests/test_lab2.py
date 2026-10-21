"""
PyMart Analytics — Зертханалық жұмыс №2 тесттері
Lambda + Closures + Recursion

pytest іске қосу:
    py -m pytest tests/test_lab2.py -v
"""

from __future__ import annotations

import pytest

from app.core.models import CartItem, Order, Product
from app.core.lab2_closures import (
    # Lambda
    square,
    add,
    is_even,
    format_prices,
    top_rated,
    sort_by_value_score,
    # Closures
    make_category_filter,
    make_price_filter,
    make_rating_filter,
    make_stock_filter,
    make_combined_filter,
    make_discount_applier,
    make_price_multiplier,
    make_order_status_filter,
    # Recursion
    find_category_in_tree,
    collect_all_category_ids,
    tree_depth,
    recursive_total,
    recursive_max,
    flatten_cart_items,
    fibonacci,
    factorial,
    aggregate_revenue_by_tree,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def products() -> tuple[Product, ...]:
    return (
        Product(id=1, name="iPhone 15",    price=450_000, category_id=1, in_stock=True,  rating=4.8),
        Product(id=2, name="Samsung S24",  price=380_000, category_id=1, in_stock=True,  rating=4.5),
        Product(id=3, name="Xiaomi 13",    price=220_000, category_id=1, in_stock=False, rating=4.2),
        Product(id=4, name="Nike Air Max", price=55_000,  category_id=2, in_stock=True,  rating=4.7),
        Product(id=5, name="Adidas Ultra", price=48_000,  category_id=2, in_stock=True,  rating=4.3),
        Product(id=6, name="Python кітабі",price=8_500,   category_id=3, in_stock=True,  rating=4.9),
    )


@pytest.fixture
def category_tree() -> list:
    return [
        {
            "id": 1,
            "name": "Электроника",
            "children": [
                {"id": 11, "name": "Телефондар",  "children": []},
                {"id": 12, "name": "Ноутбуктер",  "children": [
                    {"id": 121, "name": "Gaming",  "children": []},
                ]},
            ],
        },
        {"id": 2, "name": "Спорт",       "children": []},
        {"id": 3, "name": "Кітаптар",    "children": []},
    ]


@pytest.fixture
def orders(products) -> tuple[Order, ...]:
    from app.core.cart import add_item, checkout
    import dataclasses
    cart = ()
    cart = add_item(cart, products[0], 1)
    cart = add_item(cart, products[3], 2)
    o1 = dataclasses.replace(checkout(1, "Айгерім", cart), status="paid")
    o2 = checkout(2, "Нұрлан", cart)  # pending
    return (o1, o2)


# ---------------------------------------------------------------------------
# 1. Lambda тесттері
# ---------------------------------------------------------------------------

class TestLambda:
    def test_square(self):
        assert square(5) == 25
        assert square(0) == 0

    def test_add(self):
        assert add(3, 4) == 7

    def test_is_even(self):
        assert is_even(4) is True
        assert is_even(7) is False

    def test_format_prices(self, products):
        formatted = format_prices(products)
        assert len(formatted) == 6
        assert "iPhone 15" in formatted[0]
        assert "₸" in formatted[0]

    def test_top_rated(self, products):
        result = top_rated(products, threshold=4.5)
        assert all(p.rating >= 4.5 for p in result)
        assert len(result) == 4  # iPhone(4.8), Samsung(4.5), Nike(4.7), Python(4.9)

    def test_sort_by_value_score(self, products):
        result = sort_by_value_score(products)
        # Бағасы жоғары бірақ рейтингі төмен өнімдер соңында
        assert len(result) == len(products)


# ---------------------------------------------------------------------------
# 2. Closure тесттері
# ---------------------------------------------------------------------------

class TestClosures:
    def test_category_filter_captures_id(self, products):
        """Жабылу category_id-ті жабады."""
        phones = make_category_filter(1)
        result = tuple(filter(phones, products))
        assert len(result) == 3
        assert all(p.category_id == 1 for p in result)

    def test_category_filter_independence(self, products):
        """Екі түрлі жабылу бір-біріне әсер етпейді."""
        phones_filter  = make_category_filter(1)
        sports_filter  = make_category_filter(2)
        phones = tuple(filter(phones_filter, products))
        sports = tuple(filter(sports_filter, products))
        assert len(phones) == 3
        assert len(sports) == 2
        assert set(p.id for p in phones).isdisjoint(p.id for p in sports)

    def test_price_filter_range(self, products):
        cheap = make_price_filter(max_price=50_000)
        result = tuple(filter(cheap, products))
        assert all(p.price <= 50_000 for p in result)

    def test_price_filter_min_max(self, products):
        mid = make_price_filter(min_price=40_000, max_price=100_000)
        result = tuple(filter(mid, products))
        assert all(40_000 <= p.price <= 100_000 for p in result)

    def test_rating_filter(self, products):
        high = make_rating_filter(4.7)
        result = tuple(filter(high, products))
        assert all(p.rating >= 4.7 for p in result)

    def test_stock_filter(self, products):
        in_stock = make_stock_filter(True)
        out_stock = make_stock_filter(False)
        assert len(tuple(filter(in_stock, products))) == 5
        assert len(tuple(filter(out_stock, products))) == 1

    def test_combined_filter(self, products):
        """Бірнеше жабылу AND логикасымен."""
        combined = make_combined_filter(
            make_category_filter(1),
            make_price_filter(max_price=400_000),
            make_rating_filter(4.5),
        )
        result = tuple(filter(combined, products))
        # Samsung S24: cat=1, price=380_000, rating=4.5 ✓
        assert all(p.category_id == 1 for p in result)
        assert all(p.price <= 400_000 for p in result)
        assert all(p.rating >= 4.5 for p in result)

    def test_discount_applier_closure(self, products):
        """make_discount_applier percent-ті жабады."""
        apply_10 = make_discount_applier(10)
        apply_50 = make_discount_applier(50)
        p = products[0]  # 450_000
        assert apply_10(p).price == pytest.approx(405_000.0)
        assert apply_50(p).price == pytest.approx(225_000.0)
        assert p.price == 450_000  # бастапқы өзгермейді

    def test_price_multiplier_closure(self):
        """make_price_multiplier factor-ды жабады."""
        double = make_price_multiplier(2.0)
        half   = make_price_multiplier(0.5)
        assert double(100.0) == 200.0
        assert half(100.0)   == 50.0

    def test_order_status_filter(self, orders):
        paid_filter = make_order_status_filter("paid")
        paid = tuple(filter(paid_filter, orders))
        assert len(paid) == 1
        assert paid[0].status == "paid"

    def test_closure_factory_different_instances(self):
        """Фабрика әр шақырғанда жаңа жабылу жасайды."""
        f1 = make_price_multiplier(2.0)
        f2 = make_price_multiplier(3.0)
        assert f1 is not f2
        assert f1(10) == 20.0
        assert f2(10) == 30.0


# ---------------------------------------------------------------------------
# 3. Рекурсия тесттері
# ---------------------------------------------------------------------------

class TestRecursion:
    def test_find_category_root(self, category_tree):
        result = find_category_in_tree(category_tree, target_id=1)
        assert result is not None
        assert result["name"] == "Электроника"

    def test_find_category_nested(self, category_tree):
        """Тереңірек деңгейден іздеу."""
        result = find_category_in_tree(category_tree, target_id=11)
        assert result is not None
        assert result["name"] == "Телефондар"

    def test_find_category_deep(self, category_tree):
        """3-деңгей тереңдіктен іздеу."""
        result = find_category_in_tree(category_tree, target_id=121)
        assert result is not None
        assert result["name"] == "Gaming"

    def test_find_category_not_found(self, category_tree):
        result = find_category_in_tree(category_tree, target_id=999)
        assert result is None

    def test_collect_all_ids(self, category_tree):
        ids = collect_all_category_ids(category_tree)
        assert set(ids) == {1, 11, 12, 121, 2, 3}

    def test_collect_empty(self):
        assert collect_all_category_ids([]) == []

    def test_tree_depth(self, category_tree):
        # Ең терең: 1 → 12 → 121 = 3 деңгей
        assert tree_depth(category_tree) == 3

    def test_tree_depth_empty(self):
        assert tree_depth([]) == 0

    def test_recursive_total(self):
        assert recursive_total([1.0, 2.0, 3.0]) == pytest.approx(6.0)
        assert recursive_total([]) == 0.0
        assert recursive_total([5.5]) == pytest.approx(5.5)

    def test_recursive_max(self):
        assert recursive_max([3.0, 1.0, 4.0, 1.0, 5.0]) == pytest.approx(5.0)
        assert recursive_max([7.0]) == pytest.approx(7.0)

    def test_flatten_cart_items(self, products):
        from app.core.cart import add_item
        cart: tuple = ()
        cart = add_item(cart, products[0], 1)
        cart = add_item(cart, products[1], 2)
        nested = [list(cart[:1]), [list(cart[1:])]]
        flat = flatten_cart_items(nested)
        assert len(flat) == 2
        assert all(isinstance(i, CartItem) for i in flat)

    def test_fibonacci(self):
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1
        assert fibonacci(10) == 55
        assert fibonacci(20) == 6765

    def test_fibonacci_memoization(self):
        """lru_cache — қайталап шақырғанда жылдамырақ (cache_info тексеру)."""
        fibonacci.cache_clear()
        fibonacci(30)
        info = fibonacci.cache_info()
        assert info.currsize > 0  # кэш жұмыс жасады

    def test_factorial(self):
        assert factorial(0) == 1
        assert factorial(5) == 120
        assert factorial(10) == 3628800

    def test_aggregate_revenue_by_tree(self, products, category_tree):
        orders_by_product = {1: 450_000.0, 4: 110_000.0, 6: 8_500.0}
        result = aggregate_revenue_by_tree(
            category_tree, products, orders_by_product
        )
        # Категория 1 (Электроника): iPhone = 450_000
        assert result[1] == pytest.approx(450_000.0)
        # Категория 2 (Спорт): Nike = 110_000
        assert result[2] == pytest.approx(110_000.0)
        # Категория 3 (Кітаптар): Python кітабі = 8_500
        assert result[3] == pytest.approx(8_500.0)
