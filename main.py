# pyright: reportMissingTypeArgument = false
# pyright: reportUnknownArgumentType = false
# pyright: reportUnknownLambdaType = false
# pyright: reportUnknownVariableType = false
# pyright: reportUnknownMemberType  = false
# pyright: reportUnknownParameterType = false
# pyright: reportAny = false

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
    '''
    Parameters for the HTTP request to the Flixbus API.

    :param from_city_id: UUID representing the departure city.
    :param to_city_id: UUID representing the destination city.
    :param departure_date: Date of departure in the format DD.MM.YYYY.
    :param products: JSON string specifying how many adults, children, bikes, et c. to include in the query.
    :param currency: Currency code used for the search.
    :param locale: Language and region setting for the response.
    :param search_by: Likely the method to search for routes (in this case, 'cities').
    :param include_after_midnight_rides: Whether to include rides arriving after midnight.
    '''
    params = {
        'from_city_id': '490d29d8-7151-4e05-86df-68fba4f000be',  # Los Angeles, CA
        'to_city_id': '30e3dcd2-f9a7-4900-8f39-7a77c261904e',  # Las Vegas, NV
        'departure_date': (
            datetime.datetime.now() + datetime.timedelta(days=7)
        ).strftime(r'%d.%m.%Y'),
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
    '''
    Mimics the behavior of the JavaScript function getPlatformFee by determining the appropriate additional fee based on global platform fees and feature flags.

    No one should charge more for bus service based on opaque flags.
    '''
    gen = (
        float(t.get('fee_amount', '0'))
        for t in get_info(currency).get('global_platform_fees', [])
        if t.get('abTestFlag') is None
    )
    return next(gen, 0)


@functools.cache
def load_conversion_rates() -> dict[str, float]:
    '''
    Fetches the latest currency conversion rates from an external API and returns them as a dictionary mapping currency codes to their respective rates relative to the base currency.
    '''
    response = requests.get(
        f'https://v6.exchangerate-api.com/v6/c42b6ac038130001a023e5a4/latest/%s' % BASE_CURRENCY
    )
    return response.json()['conversion_rates']


def convert_to_base(value: float, currency: str = BASE_CURRENCY) -> float:
    return value / load_conversion_rates()[currency]


def get_prices(currency: str = BASE_CURRENCY) -> tuple[list[float], float] | None:
    '''
    Retrieves the prices of available bus trips and the additional platform fee for the specified currency.

    Args:
        currency(str): The currency code to use for pricing information. Defaults to BASE_CURRENCY.

    Returns:
        tuple[list[float], float] | None: A tuple containing a list of trip prices and the additional platform fee. Returns None if no trip data is available.
    '''
    extra = get_additional_fee(currency)
    trips = get_trips(currency)
    if len(trips) == 0:
        return None

    original_prices = [
        v['price']['original']
        for tr in trips
        for v in tr['results'].values()
    ]

    return (
        [
            convert_to_base(price + extra, currency)
            for price in original_prices
            if price > 0
        ],
        convert_to_base(extra, currency),
    )


if __name__ == '__main__':
    price_dict = {
        c: p
        for c in FLIXBUS_CURRENCIES
        if (p := get_prices(c)) is not None
    }
    price_list = sorted(
        price_dict.items(),
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

            BASE_CURRENCY,

            # Appended extra charge
            (
                f' ({extra:+.2f} inc.)'
                if extra > 0
                else ''
            ),
        ))
