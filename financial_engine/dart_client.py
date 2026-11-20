
import json
import os
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError


DART_URL = (
    "https://opendart.fss.or.kr/api/"
    "fnlttSinglAcntAll.json"
)

COMPANIES = {
    "Samsung Electronics": "00126380",
    "SK Hynix": "00164779",
    "Hyundai Motor": "00164742",
}

YEARS = [2022, 2023, 2024]


def get_api_key():
    key = os.getenv("OPENDART_API_KEY")

    if key:
        return key

    try:
        import streamlit as st
        return st.secrets["OPENDART_API_KEY"]
    except (ImportError, KeyError, FileNotFoundError):
        raise RuntimeError(
            "OpenDART API key is not configured"
        ) from None


def fetch_financial_statement(corp_code, year):
    if year < 2015:
        raise ValueError("Unsupported financial year")

    params = {
        "crtfc_key": get_api_key(),
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": "11011",
        "fs_div": "CFS",
    }

    url = DART_URL + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(
            url, timeout=20
        ) as response:
            data = json.load(response)

    except (HTTPError, URLError, TimeoutError):
        raise RuntimeError(
            "OpenDART request failed"
        ) from None

    if data.get("status") != "000":
        raise RuntimeError(
            "OpenDART returned status: "
            + str(data.get("status"))
        )

    rows = data.get("list", [])

    if not rows:
        raise ValueError(
            "No financial statement rows returned"
        )

    return rows


def fetch_company_history(corp_code):
    history = {}

    for year in YEARS:
        history[year] = fetch_financial_statement(
            corp_code, year
        )

    return history
