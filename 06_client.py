import platform
import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta

class HttpError(Exception):
    pass

async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    try:
                        result = await resp.json()
                        return result
                    except aiohttp.ContentTypeError:
                        raise HttpError(f"Invalid content type for {url}")
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f"Connection error: {url} - {str(err)}")

def extract_currency_rate(data: dict, currency: str) -> dict:
    for rate in data.get("exchangeRate", []):
        if rate.get("currency") == currency:
            return {
                "purchase": rate.get("purchaseRate", 0.0),
                "sale": rate.get("saleRate", 0.0),
            }
    return {"purchase": 0.0, "sale": 0.0}

async def main(index_day: int):
    data = []
    if not (1 <= index_day <= 10):
        raise ValueError("The number of days should be between 1 and 10")
    else:
        for i in range(index_day):
            d = datetime.now() - timedelta(days=i)
            shift = d.strftime("%d.%m.%Y")

            try:
                response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?json&date={shift}')
                data.append({shift: {
                    "EUR": extract_currency_rate(response, "EUR"),
                    "USD": extract_currency_rate(response, "USD"),
                }})
            except HttpError as err:
                print(err)
                return None
        return data

if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import argparse
    parser = argparse.ArgumentParser(description="Fetch currency rates from PrivatBank")
    parser.add_argument("days", type=int, help="Number of days to fetch rates for (1-10)")
    args = parser.parse_args()

    r = asyncio.run(main(args.days))
    print(r)
