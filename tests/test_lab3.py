"""
PyMart Analytics — Зертханалық жұмыс №3 тесттері
Күрделі рекурсия + Мемоизация

pytest іске қосу:
    py -m pytest tests/test_lab3.py -v
"""

from __future__ import annotations

import time

import pytest

from app.core.models import Product
from app.core.lab3_memo import (
    # Өз мемоизация
    memoize,
    # Баяу (мемоизациясыз)
    fib_slow,
    count_paths_slow,
    # Жылдам (мемоизациялы)
    fib_fast,
    count_paths_fast,
    # Жоба деректері
    find_similar_products,
    count_discount_combinations,
    generate_discount_packages,
    longest_growth_sequence,
    hanoi_moves,
    hanoi_count,
    max_order_value,
    # Benchmark
    compare_fib,
    compare_paths,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_caches():
    """Әр тест алдында кэшті тазалайды."""
    fib_fast.cache_clear()
    count_paths_fast.cache_clear()
    count_discount_combinations.cache_clear()
    longest_growth_sequence.cache_clear()
    hanoi_count.cache_clear()
    max_order_value.cache_clear()
    yield


@pytest.fixture
def products() -> tuple[Product, ...]:
    return (
        Product(id=1, name="iPhone 15",     price=450_000, category_id=1, in_stock=True,  rating=4.8),
        Product(id=2, name="Samsung S24",   price=380_000, category_id=1, in_stock=True,  rating=4.5),
        Product(id=3, name="Xiaomi 13",     price=220_000, category_id=1, in_stock=False, rating=4.2),
        Product(id=4, name="Nike Air Max",  price=55_000,  category_id=2, in_stock=True,  rating=4.7),
        Product(id=5, name="Adidas Ultra",  price=48_000,  category_id=2, in_stock=True,  rating=4.3),
        Product(id=6, name="Python кітабі", price=8_500,   category_id=3, in_stock=True,  rating=4.9),
    )


# ===========================================================================
# 1. ӨЗ МЕМОИЗАЦИЯ ДЕКОРАТОРЫ
# ===========================================================================

class TestCustomMemoize:
    def test_memoize_basic(self):
        """Кэш жұмыс жасайды — нәтиже сақталады."""
        call_count = [0]

        @memoize
        def expensive(n: int) -> int:
            call_count[0] += 1
            return n * n

        assert expensive(5) == 25
        assert expensive(5) == 25   # кэштен
        assert call_count[0] == 1   # тек 1 рет шақырылды

    def test_memoize_different_args(self):
        """Әр аргумент жеке кэшке сақталады."""
        @memoize
        def double(n: int) -> int:
            return n * 2

        assert double(3) == 6
        assert double(4) == 8
        assert double.cache_info() == 2  # 2 жазба

    def test_memoize_cache_clear(self):
        """cache_clear() кэшті толық тазалайды."""
        call_count = [0]

        @memoize
        def fn(n: int) -> int:
            call_count[0] += 1
            return n

        fn(10)
        assert call_count[0] == 1
        fn.cache_clear()
        fn(10)
        assert call_count[0] == 2   # қайта есептелді

    def test_memoize_preserves_function_name(self):
        """@wraps арқылы функция атауы сақталады."""
        @memoize
        def my_function(x):
            return x
        assert my_function.__name__ == "my_function"


# ===========================================================================
# 2. ФИБОНАЧЧИ — ДЕЙІН / КЕЙІН
# ===========================================================================

class TestFibonacci:
    def test_fib_slow_correctness(self):
        assert fib_slow(0) == 0
        assert fib_slow(1) == 1
        assert fib_slow(10) == 55
        assert fib_slow(20) == 6765

    def test_fib_fast_correctness(self):
        assert fib_fast(0) == 0
        assert fib_fast(1) == 1
        assert fib_fast(10) == 55
        assert fib_fast(30) == 832040
        assert fib_fast(50) == 12586269025

    def test_fib_slow_vs_fast_same_result(self):
        """Екеуі де бірдей нәтиже береді."""
        for n in range(20):
            assert fib_slow(n) == fib_fast(n)

    def test_fib_fast_uses_cache(self):
        """lru_cache жұмыс жасайды — cache_info тексеру."""
        fib_fast(30)
        info = fib_fast.cache_info()
        assert info.currsize > 0
        assert info.hits > 0   # кэш хиттері болды

    def test_fib_fast_speedup(self):
        """
        Өнімділік тест: lru_cache нұсқасы баяуға қарағанда жылдам.
        n=30 үшін speedup > 100x.
        """
        result = compare_fib(30)
        assert result["result"] == 832040
        # Мемоизациялы нұсқа кемінде 10x жылдам болуы керек
        assert result["speedup"] == "∞" or result["speedup"] >= 10

    def test_fib_large_n(self):
        """Мемоизациямен n=100 жылдам есептеледі."""
        start = time.perf_counter()
        result = fib_fast(100)
        elapsed = time.perf_counter() - start
        assert result == 354224848179261915075
        assert elapsed < 0.1   # 100 мс-тан аз


# ===========================================================================
# 3. ТОРДА ЖОЛ САНАУ — ДЕЙІН / КЕЙІН
# ===========================================================================

class TestGridPaths:
    def test_paths_slow_base_cases(self):
        assert count_paths_slow(1, 1) == 1
        assert count_paths_slow(1, 5) == 1
        assert count_paths_slow(5, 1) == 1

    def test_paths_fast_correctness(self):
        assert count_paths_fast(1, 1) == 1
        assert count_paths_fast(3, 3) == 6
        assert count_paths_fast(4, 4) == 20
        assert count_paths_fast(10, 10) == 48620

    def test_paths_slow_vs_fast_same_result(self):
        for r in range(1, 7):
            for c in range(1, 7):
                assert count_paths_slow(r, c) == count_paths_fast(r, c)

    def test_paths_fast_cache_stored(self):
        count_paths_fast(8, 8)
        assert count_paths_fast.cache_info() > 0

    def test_paths_speedup(self):
        """Өз memoize: 10×10 торда speedup > 10x."""
        result = compare_paths(15, 15)
        assert result["result"] == 40116600
        assert result["speedup"] >= 10 or result["time_slow_ms"] > result["time_fast_ms"]


# ===========================================================================
# 4. ЖОБА ДЕРЕКТЕРІНЕ МЕМОИЗАЦИЯ
# ===========================================================================

class TestProjectMemo:
    def test_find_similar_products(self, products):
        """Бір категориядағы ұқсас өнімдер табылады."""
        similar = find_similar_products(products, target_id=1, depth=1)
        # iPhone(1) → Samsung(2), Xiaomi(3) бір категорияда
        assert 2 in similar
        assert 3 in similar
        assert 1 not in similar   # өзі болмауы керек

    def test_find_similar_cached(self, products):
        """Бірдей сұраныс кэштен алынады."""
        find_similar_products(products, target_id=1, depth=1)
        size_before = len(find_similar_products.cache)  # type: ignore
        find_similar_products(products, target_id=1, depth=1)
        size_after = len(find_similar_products.cache)   # type: ignore
        assert size_before == size_after   # кэш өсмеді

    def test_find_similar_different_category(self, products):
        """Басқа категориядағы өнімдер ұқсас емес."""
        similar = find_similar_products(products, target_id=4, depth=1)
        # Nike(4) → тек Adidas(5) бір категорияда
        assert 5 in similar
        assert 1 not in similar   # iPhone басқа категория

    def test_count_discount_combinations(self):
        """C(n,k) Паскаль үшбұрышымен сәйкес."""
        assert count_discount_combinations(10, 3) == 120
        assert count_discount_combinations(5, 2) == 10
        assert count_discount_combinations(6, 0) == 1
        assert count_discount_combinations(6, 6) == 1

    def test_count_discount_combinations_cached(self):
        """lru_cache жұмыс жасайды."""
        count_discount_combinations(10, 5)
        info = count_discount_combinations.cache_info()
        assert info.currsize > 0
        assert info.hits > 0

    def test_generate_discount_packages(self, products):
        """3 өнімнен тұратын пакеттер генерациясы."""
        packages = generate_discount_packages(products, package_size=2)
        # C(6,2) = 15 пакет
        assert len(packages) == 15
        assert all(len(pkg) == 2 for pkg in packages)

    def test_generate_packages_all_unique(self, products):
        """Барлық пакеттер бірегей."""
        packages = generate_discount_packages(products, package_size=2)
        ids_set = {tuple(p.id for p in pkg) for pkg in packages}
        assert len(ids_set) == len(packages)

    def test_longest_growth_sequence(self):
        """LIS: ең ұзын өсу тізбегі."""
        prices = (100.0, 200.0, 150.0, 300.0, 250.0, 400.0)
        # 100 → 200 → 300 → 400 = ұзындығы 4
        result = longest_growth_sequence(prices, 0)
        assert result >= 4

    def test_longest_growth_all_increasing(self):
        prices = (1.0, 2.0, 3.0, 4.0, 5.0)
        assert longest_growth_sequence(prices, 0) == 5

    def test_longest_growth_all_decreasing(self):
        prices = (5.0, 4.0, 3.0, 2.0, 1.0)
        assert longest_growth_sequence(prices, 0) == 1

    def test_longest_growth_cached(self):
        """memoize кэші жұмыс жасайды."""
        prices = (10.0, 20.0, 15.0, 30.0)
        longest_growth_sequence.cache_clear()
        longest_growth_sequence(prices, 0)
        assert longest_growth_sequence.cache_info() > 0


# ===========================================================================
# 5. ХАНОЙ МҰНАРАСЫ
# ===========================================================================

class TestHanoi:
    def test_hanoi_moves_n1(self):
        moves = hanoi_moves(1)
        assert moves == ["A → C"]

    def test_hanoi_moves_n2(self):
        moves = hanoi_moves(2)
        assert len(moves) == 3
        assert moves == ["A → B", "A → C", "B → C"]

    def test_hanoi_moves_n3(self):
        assert len(hanoi_moves(3)) == 7

    def test_hanoi_count_formula(self):
        """2^n - 1 формуласымен сәйкес."""
        for n in range(1, 10):
            assert hanoi_count(n) == 2 ** n - 1

    def test_hanoi_count_cached(self):
        hanoi_count(10)
        info = hanoi_count.cache_info()
        assert info.currsize > 0


# ===========================================================================
# 6. РЕКУРСИВТІ РЮКЗАК (MAX ORDER VALUE)
# ===========================================================================

class TestKnapsack:
    def test_max_order_value_basic(self):
        totals = (100_000.0, 200_000.0, 150_000.0, 300_000.0)
        # Бюджет 350_000: 100_000 + 200_000 = 300_000 немесе 150_000+200_000=350_000
        result = max_order_value(totals, 350_000.0)
        assert result == pytest.approx(350_000.0)

    def test_max_order_value_empty(self):
        assert max_order_value((), 100_000.0) == 0.0

    def test_max_order_value_zero_capacity(self):
        totals = (100_000.0, 200_000.0)
        assert max_order_value(totals, 0.0) == 0.0

    def test_max_order_value_all_fit(self):
        totals = (10_000.0, 20_000.0, 30_000.0)
        result = max_order_value(totals, 100_000.0)
        assert result == pytest.approx(60_000.0)

    def test_max_order_value_cached(self):
        totals = (50_000.0, 100_000.0, 150_000.0, 200_000.0)
        max_order_value(totals, 250_000.0)
        info = max_order_value.cache_info()
        assert info.currsize > 0
        assert info.hits > 0   # рекурсия кэштен пайдаланды


# ===========================================================================
# 7. BENCHMARK ИНТЕГРАЦИЯЛЫҚ ТЕСТ
# ===========================================================================

class TestBenchmark:
    def test_compare_fib_output_keys(self):
        result = compare_fib(25)
        assert "n" in result
        assert "result" in result
        assert "time_slow_ms" in result
        assert "time_fast_ms" in result
        assert "speedup" in result

    def test_compare_fib_correct_value(self):
        result = compare_fib(25)
        assert result["result"] == 75025

    def test_compare_paths_output_keys(self):
        result = compare_paths(10, 10)
        assert "grid" in result
        assert result["grid"] == "10×10"
        assert result["result"] == 48620

    def test_fast_always_faster_or_equal(self):
        """Мемоизациялы нұсқа баяудан асып кетпейді."""
        result = compare_fib(30)
        # time_fast_ms ≤ time_slow_ms (немесе speedup ≥ 1)
        assert (
            result["speedup"] == "∞"
            or result["speedup"] >= 1
        )
