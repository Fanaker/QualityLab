"""Small shop domain used as the system under test (SUT)."""
from decimal import Decimal

CATALOG = {
    "SKU-104": {"name": "Auriculares Wave", "price": "89.90", "stock": 42},
    "SKU-205": {"name": "Teclado Pulse", "price": "179.00", "stock": 23},
    "SKU-312": {"name": "Mouse Core", "price": "59.50", "stock": 70},
}

class ShopError(ValueError):
    pass


def quote_order(sku: str, quantity: int, coupon: str = "") -> dict:
    if sku not in CATALOG:
        raise ShopError("El producto no existe")
    if type(quantity) is not int or quantity < 1 or quantity > 25:
        raise ShopError("La cantidad debe estar entre 1 y 25")
    product = CATALOG[sku]
    if quantity > product["stock"]:
        raise ShopError("Stock insuficiente")
    if coupon and coupon != "BIENVENIDO10":
        raise ShopError("Cupón no válido")
    subtotal = Decimal(product["price"]) * quantity
    discount = (subtotal * Decimal("0.10")).quantize(Decimal("0.01")) if coupon else Decimal("0")
    return {"sku": sku, "quantity": quantity, "subtotal": float(subtotal), "discount": float(discount), "total": float(subtotal - discount)}
