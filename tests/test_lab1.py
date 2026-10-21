"""
PyMart Analytics — тесттер
Зертханалық жұмыс №1: pytest

pytest-ті іске қосу:
    py -m pytest tests/ -v
"""

import dataclasses

import pytest

from app.core.cart import (
    add_item,
    apply_discount_to_cart,
    cart_item_count,
    cart_total,
    checkout,
    remove_item,
    update_quantity,
)
from app.core.catalog import (
    apply_discount,
    apply_discount_to_all,
    average_price,
    filter_by_category,
    filter_in_stock,
    get_names,
    search_by_name,
    sort_by,
    total_catalog_value,
    update_rating,
)
from app.core.models import CartItem, Discount, Order, Product
from app.core.reports import (
    average_order_value,
    build_sales_report,
    category_report,
    paid_orders,
    top_selling_product_id,
    total_revenue,
)
from app.pipelines.product_pipeline import (
    catalog_pipeline,
    compose,
    discount_pipeline,
    pipe,
    summary_pipeline,
)

# ---------------------------------------------------------------------------
# Fixture — тест деректері
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_products() -> tuple[Product, ...]:
    return (
        Product(id=1, name="iPhone 15",     price=450_000, category_id=1, in_stock=True,  rating=4.8),
        Product(id=2, name="Samsung S24",   price=380_000, category_id=1, in_stock=True,  rating=4.5),
        Product(id=3, name="Xiaomi 13",     price=220_000, category_id=1, in_stock=False, rating=4.2),
        Product(id=4, name="Nike Air Max",  price=55_000,  category_id=2, in_stock=True,  rating=4.7),
        Product(id=5, name="Adidas Ultra",  price=48_000,  category_id=2, in_stock=True,  rating=4.3),
        Product(id=6, name="Python книгі",  price=8_500,   category_id=3, in_stock=True,  rating=4.9),
    )


@pytest.fixture
def sample_cart(sample_products) -> tuple[CartItem, ...]:
    cart: tuple[CartItem, ...] = ()
    cart = add_item(cart, sample_products[0], 1)  # iPhone x1
    cart = add_item(cart, sample_products[3], 2)  # Nike x2
    return cart


@pytest.fixture
def sample_orders(sample_cart) -> tuple[Order, ...]:
    o1 = checkout(1, "Айгерім Бекова", sample_cart)
    o1 = dataclasses.replace(o1, status="paid")
    o2 = checkout(2, "Нұрлан Сейткали", sample_cart)
    # o2 — pending (төленбеген)
    return (o1, o2)


# ---------------------------------------------------------------------------
# 1. Модель тесттері — иммутабельділік
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_product_is_immutable(self, sample_products):
        """Product өзгертуге болмайды."""
        p = sample_products[0]
        with pytest.raises(AttributeError):
            p.price = 999  # type: ignore[misc]

    def test_order_is_frozen(self, sample_cart):
        """Order frozen dataclass — тікелей меншіктеу AttributeError шығарады."""
        order = checkout(1, "Тест", sample_cart)
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            order.status = "paid"  # type: ignore[misc]

    def test_replace_creates_new_object(self, sample_products):
        """_replace жаңа нысан жасайды, бастапқы өзгермейді."""
        original = sample_products[0]
        discounted = apply_discount(original, 10)
        assert original.price == 450_000
        assert discounted.price == 405_000.0
        assert original is not discounted


# ---------------------------------------------------------------------------
# 2. Каталог таза функциялары
# ---------------------------------------------------------------------------

class TestCatalogPureFunctions:
    def test_apply_discount_pure(self, sample_products):
        p = sample_products[0]
        result = apply_discount(p, 20)
        assert result.price == 360_000.0
        assert p.price == 450_000  # бастапқы өзгермеді

    def test_update_rating_valid(self, sample_products):
        p = sample_products[0]
        updated = update_rating(p, 3.5)
        assert updated.rating == 3.5

    def test_update_rating_invalid(self, sample_products):
        with pytest.raises(ValueError):
            update_rating(sample_products[0], 6.0)

    def test_filter_by_category(self, sample_products):
        phones = filter_by_category(sample_products, category_id=1)
        assert len(phones) == 3
        assert all(p.category_id == 1 for p in phones)

    def test_filter_in_stock(self, sample_products):
        in_stock = filter_in_stock(sample_products)
        assert len(in_stock) == 5  # Xiaomi 13 қоймада жоқ
        assert all(p.in_stock for p in in_stock)

    def test_apply_discount_to_all(self, sample_products):
        discounted = apply_discount_to_all(sample_products, 10)
        assert len(discounted) == len(sample_products)
        assert discounted[0].price == pytest.approx(405_000.0)

    def test_get_names(self, sample_products):
        names = get_names(sample_products)
        assert "iPhone 15" in names

    def test_total_catalog_value(self, sample_products):
        total = total_catalog_value(sample_products)
        expected = 450_000 + 380_000 + 220_000 + 55_000 + 48_000 + 8_500
        assert total == expected

    def test_average_price_empty(self):
        assert average_price(()) == 0.0

    def test_sort_by_price(self, sample_products):
        sorted_p = sort_by(sample_products, key_fn=lambda p: p.price)
        assert sorted_p[0].price <= sorted_p[-1].price

    def test_search_by_name(self, sample_products):
        result = search_by_name(sample_products, "iphone")
        assert len(result) == 1
        assert result[0].name == "iPhone 15"


# ---------------------------------------------------------------------------
# 3. Себет таза функциялары
# ---------------------------------------------------------------------------

class TestCartPureFunctions:
    def test_add_item_creates_new_cart(self, sample_products):
        cart: tuple[CartItem, ...] = ()
        new_cart = add_item(cart, sample_products[0])
        assert len(new_cart) == 1
        assert cart == ()  # бастапқы өзгермеді

    def test_add_existing_item_increases_quantity(self, sample_products):
        cart: tuple[CartItem, ...] = ()
        cart = add_item(cart, sample_products[0], 2)
        cart = add_item(cart, sample_products[0], 3)
        assert cart[0].quantity == 5

    def test_remove_item(self, sample_cart, sample_products):
        new_cart = remove_item(sample_cart, product_id=1)
        assert all(item.product.id != 1 for item in new_cart)

    def test_update_quantity_zero_removes(self, sample_cart):
        new_cart = update_quantity(sample_cart, product_id=1, new_quantity=0)
        assert all(item.product.id != 1 for item in new_cart)

    def test_cart_total(self, sample_cart):
        # iPhone 450_000 x1 + Nike 55_000 x2
        expected = 450_000 + 55_000 * 2
        assert cart_total(sample_cart) == pytest.approx(expected)

    def test_cart_item_count(self, sample_cart):
        assert cart_item_count(sample_cart) == 3  # 1 + 2

    def test_checkout_empty_cart(self):
        with pytest.raises(ValueError, match="бос"):
            checkout(1, "Тест", ())

    def test_checkout_creates_order(self, sample_cart):
        order = checkout(1, "Айгерім", sample_cart)
        assert order.customer_name == "Айгерім"
        assert order.status == "pending"
        assert order.total > 0

    def test_apply_discount_below_min_amount(self, sample_products):
        cart: tuple[CartItem, ...] = (CartItem(sample_products[5], 1),)  # 8_500 теңге
        discount = Discount(code="BIG50", percent=50, min_amount=100_000)
        new_cart = apply_discount_to_cart(cart, discount)
        assert new_cart[0].product.price == sample_products[5].price  # өзгерген жоқ


# ---------------------------------------------------------------------------
# 4. Есеп тесттері
# ---------------------------------------------------------------------------

class TestReports:
    def test_paid_orders_filter(self, sample_orders):
        paid = paid_orders(sample_orders)
        assert len(paid) == 1
        assert paid[0].status == "paid"

    def test_total_revenue_only_paid(self, sample_orders):
        rev = total_revenue(paid_orders(sample_orders))
        assert rev > 0

    def test_average_order_value_empty(self):
        assert average_order_value(()) == 0.0

    def test_top_selling_product(self, sample_orders):
        top = top_selling_product_id(paid_orders(sample_orders))
        assert top is not None

    def test_build_sales_report_keys(self, sample_orders):
        report = build_sales_report(sample_orders)
        assert "total_orders" in report
        assert "total_revenue" in report
        assert "average_order_value" in report

    def test_category_report_empty(self, sample_products):
        report = category_report(sample_products, category_id=999)
        assert report["product_count"] == 0

    def test_category_report_phones(self, sample_products):
        report = category_report(sample_products, category_id=1)
        assert report["product_count"] == 3
        assert report["min_price"] == 220_000
        assert report["max_price"] == 450_000


# ---------------------------------------------------------------------------
# 5. Pipeline тесттері
# ---------------------------------------------------------------------------

class TestPipelines:
    def test_catalog_pipeline_in_stock_only(self, sample_products):
        result = catalog_pipeline(sample_products)
        assert all(p.in_stock for p in result)

    def test_catalog_pipeline_by_category(self, sample_products):
        result = catalog_pipeline(sample_products, category_id=2)
        assert all(p.category_id == 2 for p in result)

    def test_catalog_pipeline_sorted(self, sample_products):
        result = catalog_pipeline(sample_products, sort_by_price=True)
        prices = [p.price for p in result]
        assert prices == sorted(prices)

    def test_discount_pipeline(self, sample_products):
        discounts = ((1, 10.0), (2, 20.0))  # телефон -10%, аяқ киім -20%
        result = discount_pipeline(sample_products, discounts)
        iphone = next(p for p in result if p.id == 1)
        assert iphone.price == pytest.approx(405_000.0)

    def test_summary_pipeline_empty(self):
        assert summary_pipeline(())["count"] == 0

    def test_summary_pipeline(self, sample_products):
        result = summary_pipeline(sample_products)
        assert result["count"] == 6
        assert result["min"] == 8_500

    def test_pipe_composition(self):
        add1 = lambda x: x + 1
        mul2 = lambda x: x * 2
        fn = pipe(add1, mul2)   # (x+1)*2
        assert fn(3) == 8

    def test_compose_order(self):
        add1 = lambda x: x + 1
        mul2 = lambda x: x * 2
        fn = compose(add1, mul2)  # mul2 алдымен: (x*2)+1
        assert fn(3) == 7
