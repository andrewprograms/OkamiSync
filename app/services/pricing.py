from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict

def to_decimal(x) -> Decimal:
    return Decimal(str(x))

def money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def compute_totals(line_items: List[Dict], tax_inclusive: bool = False, tax_rate: Decimal = Decimal("0.10")) -> dict:
    subtotal = Decimal("0.00")
    tax = Decimal("0.00")
    for li in line_items:
        qty = to_decimal(li.get("quantity", 1))
        price_each = to_decimal(li.get("price_each", "0"))
        line_sub = qty * price_each
        if tax_inclusive:
            base = (line_sub / (Decimal("1.0") + tax_rate))
            line_tax = line_sub - base
            subtotal += base
            tax += line_tax
        else:
            subtotal += line_sub
            tax += line_sub * tax_rate
    subtotal = money(subtotal)
    tax = money(tax)
    total = money(subtotal + tax)
    return {"subtotal": subtotal, "tax": tax, "total": total}
