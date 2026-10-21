"""
PyMart Analytics — Зертханалық жұмыс №3
Күрделі рекурсия + Мемоизация

Лекция 7 бойынша:
  - Күрделі рекурсивті алгоритмдер
  - lru_cache + өз мемоизация декораторы
  - Дейін/Кейін өнімділік салыстыру
"""

from __future__ import annotations

import time
from functools import lru_cache, wraps
from typing import Callable, TypeVar

from app.core.models import Product

F = TypeVar("F", bound=Callable)


# ===========================================================================
# БӨЛІМ 1: ӨЗ МЕМОИЗАЦИЯ ДЕКОРАТОРЫ
# ===========================================================================

def memoize(func: F) -> F:
    """
    Қолмен жазылған мемоизация декораторы.
    dict кэшін жабылу (closure) арқылы сақтайды.

    lru_cache-тен айырмашылығы: шексіз кэш, кілт = аргументтер кортежі.
    """
    cache: dict = {}

    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    wrapper.cache = cache                          # тестілеу үшін
    wrapper.cache_info = lambda: len(cache)        # кэш өлшемі
    wrapper.cache_clear = lambda: cache.clear()    # кэшті тазалау
    return wrapper  # type: ignore[return-value]


# ===========================================================================
# БӨЛІМ 2: МЕМОИЗАЦИЯСЫЗ БАЯУ РЕКУРСИЯ (baseline)
# ===========================================================================

def fib_slow(n: int) -> int:
    """
    Мемоизациясыз Фибоначчи — O(2^n) экспоненциалдық.
    n=35 үшін ~10 секунд.
    """
    if n <= 1:
        return n
    return fib_slow(n - 1) + fib_slow(n - 2)


def count_paths_slow(rows: int, cols: int) -> int:
    """
    Торда жол санау (мемоизациясыз) — O(2^(m+n)).
    Тек оң немесе төмен жылжуға болады.
    """
    if rows == 1 or cols == 1:
        return 1
    return count_paths_slow(rows - 1, cols) + count_paths_slow(rows, cols - 1)


# ===========================================================================
# БӨЛІМ 3: МЕМОИЗАЦИЯЛЫ ЖЫЛДАМ РЕКУРСИЯ
# ===========================================================================

@lru_cache(maxsize=None)
def fib_fast(n: int) -> int:
    """
    Мемоизациялы Фибоначчи — O(n) сызықтық.
    lru_cache: бірдей аргумент → кэштен алады.
    """
    if n <= 1:
        return n
    return fib_fast(n - 1) + fib_fast(n - 2)


@memoize
def count_paths_fast(rows: int, cols: int) -> int:
    """
    Торда жол санау — өз memoize декораторымен O(m*n).
    """
    if rows == 1 or cols == 1:
        return 1
    return count_paths_fast(rows - 1, cols) + count_paths_fast(rows, cols - 1)


# ===========================================================================
# БӨЛІМ 4: ЖОБАНЫҢ НАҚТЫ ДЕРЕКТЕРІНЕ МЕМОИЗАЦИЯ
# ===========================================================================

# ---------------------------------------------------------------------------
# 4.1 Өнімдерді рекурсивті іздеу + кэш
# ---------------------------------------------------------------------------

def _make_product_recommender():
    """
    Фабрика: ішінде мемоизацияланған ұқсас өнімдер рекомендациясы.
    category_id → ұқсас өнімдер id тізімі кэшке сақталады.
    """
    cache: dict[int, tuple[int, ...]] = {}

    def find_similar(
        products: tuple[Product, ...],
        target_id: int,
        depth: int = 2,
    ) -> tuple[int, ...]:
        """
        Рекурсивті: берілген өнімге ұқсас өнімдерді тауып,
        олардың ұқсастарын да (depth деңгейіне дейін) жинайды.
        Кэш: category_id + depth → нәтиже.
        """
        if depth == 0:
            return ()

        target = next((p for p in products if p.id == target_id), None)
        if target is None:
            return ()

        cache_key = (target.category_id, depth)
        if cache_key in cache:
            return cache[cache_key]

        # Бір категориядағы өнімдер (өзін шығарып)
        similar_ids = tuple(
            p.id for p in products
            if p.category_id == target.category_id and p.id != target_id
        )

        # Рекурсия: ұқсас өнімдердің де ұқсастарын алу
        extended: set[int] = set(similar_ids)
        for sid in similar_ids:
            extended.update(find_similar(products, sid, depth - 1))
        extended.discard(target_id)

        result = tuple(sorted(extended))
        cache[cache_key] = result
        return result

    find_similar.cache = cache  # type: ignore[attr-defined]
    return find_similar


find_similar_products = _make_product_recommender()


# ---------------------------------------------------------------------------
# 4.2 Рекурсивті комбинаторика — жеңілдік пакеттері
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def count_discount_combinations(n: int, k: int) -> int:
    """
    C(n, k) — n өнімнен k-ны жеңілдікке таңдау жолдарының саны.
    Base case: k == 0 немесе k == n → 1
    Рекурсия: C(n,k) = C(n-1,k-1) + C(n-1,k)  (Паскаль үшбұрышы)

    Нақты қолданыс: 10 өнімнен 3-ін промокодқа таңдаудың жолдары.
    """
    if k == 0 or k == n:
        return 1
    if k > n:
        return 0
    return count_discount_combinations(n - 1, k - 1) + count_discount_combinations(n - 1, k)


def generate_discount_packages(
    products: tuple[Product, ...],
    package_size: int,
    index: int = 0,
    current: tuple[Product, ...] = (),
) -> list[tuple[Product, ...]]:
    """
    Рекурсивті комбинациялар генераторы.
    Base case: current өлшемі package_size-ге жеткенде → қайтар
    Recursive case: өнімдерді бір-бірлеп қосу

    Нақты қолданыс: "3 өнімнен тұратын жеңілдік пакеттерін жасау"
    """
    if len(current) == package_size:
        return [current]
    if index >= len(products):
        return []

    # Ағымдағы өнімді қосу немесе өткізіп жіберу
    include = generate_discount_packages(
        products, package_size, index + 1, current + (products[index],)
    )
    exclude = generate_discount_packages(
        products, package_size, index + 1, current
    )
    return include + exclude


# ---------------------------------------------------------------------------
# 4.3 Рекурсивті тапсырыс тарихы — ең ұзын өсу реті
# ---------------------------------------------------------------------------

@memoize
def longest_growth_sequence(prices: tuple[float, ...], index: int = 0) -> int:
    """
    LIS (Longest Increasing Subsequence) рекурсивті + мемоизация.
    Нақты қолданыс: бағалардың ең ұзын өсу тізбегін табу
    (тренд талдауы үшін).

    Base case: index >= len(prices) → 0
    """
    if index >= len(prices):
        return 0

    # Осы индекстен бастап ең ұзын өсу реті
    best = 1
    for j in range(index + 1, len(prices)):
        if prices[j] > prices[index]:
            candidate = 1 + longest_growth_sequence(prices, j)
            if candidate > best:
                best = candidate
    return best


# ---------------------------------------------------------------------------
# 4.4 Рекурсивті категория ағашы талдауы — Ханой мұнарасы принципі
# ---------------------------------------------------------------------------

def hanoi_moves(n: int, source: str = "A", target: str = "C", aux: str = "B") -> list[str]:
    """
    Ханой мұнарасы — рекурсияның классикалық мысалы.
    Base case: n == 1 → тікелей жылжыту
    Recursive: n-1 диск aux-ке, 1 диск target-ке, n-1 диск target-ке

    Нақты байланыс: категория деңгейлерін рекурсивті қайта реттеу.
    """
    if n == 1:
        return [f"{source} → {target}"]
    moves = []
    moves.extend(hanoi_moves(n - 1, source, aux, target))
    moves.append(f"{source} → {target}")
    moves.extend(hanoi_moves(n - 1, aux, target, source))
    return moves


@lru_cache(maxsize=None)
def hanoi_count(n: int) -> int:
    """Ханой мұнарасы үшін қажет минималды қадам саны = 2^n - 1."""
    if n == 1:
        return 1
    return 2 * hanoi_count(n - 1) + 1


# ---------------------------------------------------------------------------
# 4.5 Рекурсивті жоспарлау — тапсырыстарды топтастыру
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def max_order_value(
    order_totals: tuple[float, ...],
    capacity: float,
    index: int = 0,
) -> float:
    """
    Рекурсивті рюкзак есебі (0/1 Knapsack) + мемоизация.
    Нақты қолданыс: берілген бюджет шегінде максималды тапсырыс құнын таңдау.

    Base case: index >= len → 0 немесе capacity <= 0 → 0
    Recursive: тапсырысты алу немесе өткізіп жіберу
    """
    if index >= len(order_totals) or capacity <= 0:
        return 0.0

    current = order_totals[index]

    # Өткізіп жіберу
    skip = max_order_value(order_totals, capacity, index + 1)

    # Алу (егер сыяды)
    take = 0.0
    if current <= capacity:
        take = current + max_order_value(
            order_totals, capacity - current, index + 1
        )

    return max(skip, take)


# ===========================================================================
# БӨЛІМ 5: ӨНІМДІЛІК САЛЫСТЫРУ (дейін / кейін)
# ===========================================================================

def benchmark(func: Callable, *args) -> tuple[object, float]:
    """Функцияны іске қосып, нәтиже мен уақытты қайтарады."""
    start = time.perf_counter()
    result = func(*args)
    elapsed = time.perf_counter() - start
    return result, elapsed


def compare_fib(n: int) -> dict:
    """
    Фибоначчи: мемоизациясыз vs lru_cache.
    Дейін/Кейін өнімділік салыстыру.
    """
    # Кейін (жылдам)
    fib_fast.cache_clear()
    result_fast, time_fast = benchmark(fib_fast, n)

    # Дейін (баяу) — тек n <= 35 үшін
    if n <= 35:
        _, time_slow = benchmark(fib_slow, n)
    else:
        time_slow = float("inf")

    return {
        "n": n,
        "result": result_fast,
        "time_slow_ms": round(time_slow * 1000, 3),
        "time_fast_ms": round(time_fast * 1000, 3),
        "speedup": (
            round(time_slow / time_fast, 1)
            if time_fast > 0 and time_slow != float("inf")
            else "∞"
        ),
    }


def compare_paths(rows: int, cols: int) -> dict:
    """
    Торда жол санау: мемоизациясыз vs өз memoize декораторы.
    """
    count_paths_fast.cache_clear()

    result_fast, time_fast = benchmark(count_paths_fast, rows, cols)
    _, time_slow = benchmark(count_paths_slow, rows, cols)

    return {
        "grid": f"{rows}×{cols}",
        "result": result_fast,
        "time_slow_ms": round(time_slow * 1000, 3),
        "time_fast_ms": round(time_fast * 1000, 3),
        "speedup": round(time_slow / time_fast, 1) if time_fast > 0 else "∞",
    }
