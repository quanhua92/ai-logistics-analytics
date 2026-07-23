from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)

    client_id: Mapped[str] = mapped_column(String(20), index=True)
    order_date: Mapped[date] = mapped_column(Date, index=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    carrier: Mapped[str] = mapped_column(String(30), index=True)
    origin_city: Mapped[str] = mapped_column(String(80))
    destination_city: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), index=True)

    sku: Mapped[str] = mapped_column(String(40), index=True)
    product_category: Mapped[str] = mapped_column(String(30), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    order_value_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    is_promo: Mapped[int] = mapped_column(Integer)
    promo_discount_pct: Mapped[int] = mapped_column(Integer)

    region: Mapped[str] = mapped_column(String(15), index=True)
    warehouse: Mapped[str] = mapped_column(String(20), index=True)


Index("ix_orders_carrier_status", Order.carrier, Order.status)
Index("ix_orders_category_date", Order.product_category, Order.order_date)
