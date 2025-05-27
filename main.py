import datetime
import functools
import requests

BASE_CURRENCY = "EUR"

FLIXBUS_CURRENCIES = {
    "AED",
    "ALL",
    "ARS",
    "AUD",
    "BAM",
    "BGN",
    "BOB",
    "BRL",
    "CAD",
    "CHF",
    "CLP",
    "CNY",
    "COP",
    "CRC",
    "CZK",
    "DKK",
    "EUR",
    "GBP",
    "GTQ",
    "HKD",
    "HNL",
    "HUF",
    "IDR",
    "ILS",
    "INR",
    "ISK",
    "JPY",
    "KRW",
    "MKD",
    "MOP",
    "MXN",
    "MYR",
    "NIO",
    "NOK",
    "NZD",
    "PEN",
    "PHP",
    "PLN",
    "PYG",
    "QAR",
    "RON",
    "RSD",
    "RUB",
    "SAR",
    "SEK",
    "SGD",
    "THB",
    "TRY",
    "TWD",
    "UAH",
    "USD",
    "UYU",
    "VEF",
    "VND",
    "ZAR",
}


@functools.cache
def get_info(currency: str = BASE_CURRENCY) -> dict:
    params = {
        'from_city_id': '490d29d8-7151-4e05-86df-68fba4f000be',  # Los Angeles, CA
        'to_city_id': '30e3dcd2-f9a7-4900-8f39-7a77c261904e',  # Las Vegas, NV
        'departure_date': datetime.datetime.now().strftime(r'%d.%m.%Y'),
        'products': '{"adult":1}',
        'currency': currency,
        'locale': 'en_US',
        'search_by': 'cities',
        'include_after_midnight_rides': '1',
    }
    response = requests.get(
        'https://global.api.flixbus.com/search/service/v4/search',
        params=params,
    )
    return response.json()


def get_trips(currency: str = BASE_CURRENCY) -> list:
    return get_info(currency).get('trips', [])


@functools.cache
def get_additional_fee(currency: str = BASE_CURRENCY) -> float:
    return sum(
        float(t.get('fee_amount', '0'))
        for t in get_info(currency).get('global_platform_fees', [])
    )


@functools.cache
def load_conversion_rates() -> dict[str, float]:
    response = requests.get(
        f'https://v6.exchangerate-api.com/v6/c42b6ac038130001a023e5a4/latest/%s' % BASE_CURRENCY
    )
    return response.json()['conversion_rates']


@functools.cache
def convert_to_base(value: float, currency: str = BASE_CURRENCY) -> float:
    return value / load_conversion_rates()[currency]


def get_prices(currency: str = BASE_CURRENCY) -> tuple[list[float], float] | None:
    extra = get_additional_fee(currency)
    trips = get_trips(currency)
    if len(trips) == 0:
        return None

    return (
        [
            convert_to_base(v['price']['original'] + extra, currency)
            for tr in trips
            for v in tr['results'].values()
        ],
        convert_to_base(extra, currency),
    )


if __name__ == '__main__':
    price_dict = {
        c: get_prices(c)
        for c in FLIXBUS_CURRENCIES
    }
    price_list = sorted(
        filter(
            lambda t: t[1] is not None,
            price_dict.items(),
        ),
        key=lambda t: t[1][0][0],
    )

    base_prices, base_extra = price_dict[BASE_CURRENCY]
    for (c, (prices, extra)) in price_list:
        print(f"%s %7.2f%% - [%s] %s%s" % (
            # Currency string
            (
                c.upper()
                if c == BASE_CURRENCY
                else c.lower()
            ),

            # Percentage of base currency price
            100. * prices[0] / base_prices[0],

            # Converted prices for a subset of trip results
            ', '.join(f'{p:.2f}' for p in prices[:4]),

            # Appended extra charge
            (
                f'{extra:+.2f} '
                if extra > 0
                else ''
            ),

            BASE_CURRENCY,
        ))
