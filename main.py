import datetime
import functools
import requests

BASE_CURRENCY = 'USD'

FLIXBUS_CURRENCIES = {
    'EUR': "€",
    'CHF': "CHF",
    'CZK': "Kč",
    'SEK': "kr",
    'GBP': "£",
    'DKK': "kr",
    'HRK': "kn",
    'PLN': "zł",
    'HUF': "ft",
    'NOK': "kr",
    'BGN': "лв",
    'RON': "RON",
    'RSD': "RSD",
    'USD': "$",
    'ALL': "L",
    'BAM': "KM",
    'UAH': "₴",
    'MKD': "ден",
    'TRY': "₺",
    'BRL': "R$",
    'CAD': "CA$",
    'MXN': "Mex$",
    'CLP': "$"
}


@functools.cache
def get_info(currency: str = BASE_CURRENCY) -> dict:
    params = {
        'from_city_id': '490d29d8-7151-4e05-86df-68fba4f000be',
        'to_city_id': '30e3dcd2-f9a7-4900-8f39-7a77c261904e',
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
def convert_to_base(value: float, currency: str = 'USD') -> float:
    return value / load_conversion_rates()[currency]


def get_prices(currency: str = BASE_CURRENCY) -> list[float]:
    extra = get_additional_fee(currency)
    return [
        convert_to_base(v['price']['original'] + extra, currency)
        for tr in get_trips(currency)
        for v in tr['results'].values()
    ]


if __name__ == '__main__':
    price_dict = {
        c: get_prices(c)
        for c in FLIXBUS_CURRENCIES.keys()
    }
    price_list = sorted(
        filter(
            lambda t: t[1],
            price_dict.items(),
        ),
        key=lambda t: t[1],
    )

    base_prices = price_dict[BASE_CURRENCY]
    for (c, prices) in price_list:
        price_str = ', '.join(f'{p:.2f}' for p in prices[:4])
        precent = f'{100. * prices[0] / base_prices[0]: 7.2f}'
        curr_str = (
            c.upper()
            if c == BASE_CURRENCY
            else c.lower()
        )
        print(f"{curr_str} {precent}% - [{price_str}] {BASE_CURRENCY}")
