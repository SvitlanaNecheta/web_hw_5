import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any


class CurrencyRateFetcher:
    API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

    def __init__(self, days: int):
        self.days = days

    def validate_days(self):
        if not 1 <= self.days <= 10:
            raise ValueError("The number of days should be between 1 and 10")

    async def fetch_rates(self) -> List[Dict[str, Any]]:
        self.validate_days()
        tasks = []
        async with aiohttp.ClientSession() as session:
            for i in range(self.days):
                date = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')
                url = f"{self.API_URL}{date}"
                tasks.append(self.fetch_rate_for_date(session, url, date))
            return await asyncio.gather(*tasks)

    async def fetch_rate_for_date(self, session: aiohttp.ClientSession, url: str, date: str) -> Dict[str, Any]:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return {
                    date: {
                        "EUR": self.extract_currency_rate(data, "EUR"),
                        "USD": self.extract_currency_rate(data, "USD"),
                    }
                }
        except (aiohttp.ClientError, aiohttp.http_exceptions.HttpProcessingError) as e:
            return {date: {"error": str(e)}}

    @staticmethod
    def extract_currency_rate(data: Dict[str, Any], currency: str) -> Dict[str, float]:
        for rate in data.get("exchangeRate", []):
            if rate.get("currency") == currency:
                return {
                    "purchase": rate.get("purchaseRate", 0.0),
                    "sale": rate.get("saleRate", 0.0),
                }
        return {"purchase": 0.0, "sale": 0.0}


class CurrencyRatesPrinter:
    @staticmethod
    def print_rates(rates: List[Dict[str, Any]]):
        print(rates)


async def main(days: int):
    fetcher = CurrencyRateFetcher(days)
    rates = await fetcher.fetch_rates()
    printer = CurrencyRatesPrinter()
    printer.print_rates(rates)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch currency rates from PrivatBank")
    parser.add_argument(
        "days",
        type=int,
        help="Number of days to fetch rates for (1-10)",
    )
    args = parser.parse_args()

    asyncio.run(main(args.days))
