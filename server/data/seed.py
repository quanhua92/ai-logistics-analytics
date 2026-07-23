import asyncio
from pathlib import Path

import pandas as pd
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Order

CSV_PATH = Path(__file__).parent / "logistics_data.csv"


def to_date(value):
    if pd.isna(value):
        return None
    return value.date()


def load_rows() -> list[dict]:
    df = pd.read_csv(
        CSV_PATH,
        parse_dates=["order_date", "delivery_date"],
        dtype={
            "is_promo": "int64",
            "promo_discount_pct": "int64",
            "quantity": "int64",
        },
    )
    rows: list[dict] = []
    for _, r in df.iterrows():
        rows.append(
            {
                "order_id": r["order_id"],
                "client_id": r["client_id"],
                "order_date": to_date(r["order_date"]),
                "delivery_date": to_date(r["delivery_date"]),
                "carrier": r["carrier"],
                "origin_city": r["origin_city"],
                "destination_city": r["destination_city"],
                "status": r["status"],
                "sku": r["sku"],
                "product_category": r["product_category"],
                "quantity": int(r["quantity"]),
                "unit_price_usd": float(r["unit_price_usd"]),
                "order_value_usd": float(r["order_value_usd"]),
                "is_promo": int(r["is_promo"]),
                "promo_discount_pct": int(r["promo_discount_pct"]),
                "region": r["region"],
                "warehouse": r["warehouse"],
            }
        )
    return rows


async def main() -> None:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        existing = (
            await session.execute(select(func.count()).select_from(Order))
        ).scalar_one()
        if existing > 0:
            print(f"already seeded ({existing} rows) — skipping")
            return

        rows = load_rows()
        await session.execute(insert(Order), rows)
        await session.commit()
        print(f"seeded {len(rows)} orders")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
