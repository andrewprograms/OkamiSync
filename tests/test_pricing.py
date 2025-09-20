from app.services.pricing import compute_totals
from decimal import Decimal

def test_tax_exclusive():
    lines=[{"quantity":2,"price_each":"10.00"},{"quantity":1,"price_each":"5.00"}]
    res=compute_totals(lines, tax_inclusive=False, tax_rate=Decimal("0.10"))
    assert str(res["subtotal"])=="25.00"
    assert str(res["tax"])=="2.50"
    assert str(res["total"])=="27.50"

def test_tax_inclusive():
    lines=[{"quantity":1,"price_each":"11.00"}]
    res=compute_totals(lines, tax_inclusive=True, tax_rate=Decimal("0.10"))
    assert str(res["subtotal"])=="10.00"
    assert str(res["tax"])=="1.00"
    assert str(res["total"])=="11.00"