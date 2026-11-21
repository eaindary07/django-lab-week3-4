from decimal import Decimal
from django.db import transaction
from django.db.models import Q, F, Case, When, DecimalField
# from core.models import Product   # uncomment if you add Product to models.py

# ---------- Challenge 1: Q objects ----------
# (Electronics AND price > 10000) OR (DISCOUNTED AND NOT China)
def challenge1():
    return Product.objects.filter(
        Q(category__name='Electronics', price__gt=10000) |
        (Q(status='DISCOUNTED') & ~Q(warehouse_country='China'))
    )
# Explanation: Q(a, b) is AND, | is OR, ~Q negates the China check.

# ---------- Challenge 2: F + Q ----------
def challenge2():
    return Product.objects.filter(
        Q(stock_quantity__lte=F('reorder_level')) |
        Q(is_promotional=True, stock_quantity__lt=F('reorder_level') * 2)
    )
# Explanation: F() compares two columns in the database, so each product
# uses its own reorder threshold.

# ---------- Challenge 3: atomic price increase with ceiling ----------
def challenge3():
    new_price = F('price') * Decimal('1.15')
    return Product.objects.filter(category__name='Gadgets').update(
        price=Case(
            When(max_allowed_price__lt=new_price, then=F('max_allowed_price')),
            default=new_price,
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )
# Explanation: a single SQL UPDATE; the price is capped at max_allowed_price.

# ---------- Challenge 4: atomic purchase guard ----------
def purchase(product_id, x):
    with transaction.atomic():
        updated = Product.objects.filter(
            pk=product_id, stock_quantity__gte=x
        ).update(
            stock_quantity=F('stock_quantity') - x,
            total_sold=F('total_sold') + x,
            total_revenue=F('total_revenue') + F('price') * x,
        )
        if updated == 0:
            raise ValueError("Insufficient stock or product not found")
# Explanation: the stock check is in the WHERE clause, so check and update
# happen in one atomic statement. No Python `if` on stock, so no race condition.