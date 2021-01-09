#!/usr/bin/env python3
"""Module for work with assets and CBR"""

from flask import Flask, redirect, url_for, abort, request, jsonify
import requests
from lxml import etree


ANSWER_PAGE_NOT_FOUND = "This route is not found"


class Asset:
    """Class for work with assets"""
    def __init__(self, name: str, char_code: str, capital: float, interest: float):
        self.name = name
        self.char_code = char_code
        self.capital = capital
        self.interest = interest

    def calculate_revenue(self, years: int) -> float:
        """Calculate revenue by period for one asset"""
        revenue = self.capital * ((1.0 + self.interest) ** years - 1.0)
        return revenue

    def to_list(self):
        """Transform information about asset to list"""
        return [self.char_code, self.name, self.capital, self.interest]


app = Flask(__name__)
app.bank = dict()


@app.errorhandler(404)
def page_not_found(_):
    """Create response for wrong reuest"""
    return ANSWER_PAGE_NOT_FOUND, 404


@app.route("/cbr/not_avalible")
def cbr_not_avalible():
    """Create response if CBR site is not avalible"""
    return "CBR service is unavailable", 503


@app.route("/cbr/daily")
def cbr_daily():
    """Get daily courses from CBR site"""
    try:
        daily_response = requests.get("https://www.cbr.ru/eng/currency_base/daily/")
    except:
        return redirect(url_for("cbr_not_avalible"))
    if daily_response.status_code >= 400:
        return redirect(url_for("cbr_not_avalible"))
    daily_dict = parse_cbr_currency_base_daily(daily_response.text)
    return jsonify(daily_dict), 200


@app.route("/cbr/key_indicators")
def key_indicators():
    """Get key indicators from CBR site"""
    try:
        key_indicators_response = requests.get("https://www.cbr.ru/eng/key-indicators/")
    except:
        return redirect(url_for("cbr_not_avalible"))
    if key_indicators_response.status_code >= 400:
        return redirect(url_for("cbr_not_avalible"))
    key_indicators_dict = parse_cbr_key_indicators(key_indicators_response.text)
    return jsonify(key_indicators_dict)


@app.route("/api/asset/add/<string:char_code>/<string:name>/<capital>/<interest>")
def add_assets(char_code, name, capital, interest):
    """Add asset to bank"""
    try:
        capital = float(capital)
        interest = float(interest)
    except:
        redirect(url_for("page_not_found"))
    if name in app.bank:
        abort(403)
    app.bank[name] = Asset(name, char_code, capital, interest)
    return f"Asset '{name}' was successfully added", 200


@app.route("/api/asset/list")
def asset_list():
    """Get list of all assets"""
    new_list = []
    for asset_name in app.bank:
        new_list.append(app.bank[asset_name].to_list())
    new_list = sorted(new_list, key=lambda s: s[0])
    return jsonify(new_list)


@app.route("/api/asset/cleanup")
def asset_cleanup():
    """Clean list of bank assets"""
    app.bank = dict()
    return "Cleaned", 200


@app.route("/api/asset/get")
def asset_get():
    """Get list assets by names"""
    search_assets = request.args.getlist("name")
    find_assets = []
    for asset_name in search_assets:
        if asset_name in app.bank:
            find_assets.append(app.bank[asset_name].to_list())
    find_assets = sorted(find_assets, key=lambda s: s[0])
    return jsonify(find_assets)


@app.route("/api/asset/calculate_revenue")
def asset_calculate_revenue():
    """Get revenue for all assets by period"""
    search_period = request.args.getlist("period")
    try:
        daily_response = requests.get("https://www.cbr.ru/eng/currency_base/daily/")
        key_indicators_response = requests.get("https://www.cbr.ru/eng/key-indicators/")
    except:
        return redirect(url_for("cbr_not_avalible"))
    if daily_response.status_code >= 400:
        return redirect(url_for("cbr_not_avalible"))
    daily_dict = parse_cbr_currency_base_daily(daily_response.text)
    if key_indicators_response.status_code >= 400:
        return redirect(url_for("cbr_not_avalible"))
    key_indicators_dict = parse_cbr_key_indicators(key_indicators_response.text)
    for key in daily_dict:
        if key not in key_indicators_dict:
            key_indicators_dict[key] = daily_dict[key]
    key_indicators_dict['RUB'] = 1.0

    total_revenue = dict()
    for period in search_period:
        total_revenue[period] = 0
        for asset_name in app.bank:
            revenue = app.bank[asset_name].calculate_revenue(int(period))
            char_code = app.bank[asset_name].char_code
            if char_code not in key_indicators_dict:
                continue
            revenue *= key_indicators_dict[char_code]
            total_revenue[period] += revenue

    return jsonify(total_revenue)


def parse_cbr_currency_base_daily(daily_html):
    """Parse daily page of CBR site"""
    root = etree.fromstring(daily_html, etree.HTMLParser())
    documents_raw = root.xpath("//tr")[1:]
    documents = []
    for document in documents_raw:
        char_code = document.xpath(".//td[2]/text()")[0]
        rate = float(document.xpath(".//td[5]/text()")[0])
        count = float(document.xpath(".//td[3]/text()")[0])
        documents.append([char_code, rate / count])

    return dict(documents)


def parse_cbr_key_indicators(key_indicators_html):
    """Parse key_indicators page of CBR sie"""
    root = etree.fromstring(key_indicators_html, etree.HTMLParser())
    content = root.xpath("//div[@class='dropdown_content']")[0]
    main_title = content.xpath(".//div[@class='key-indicator']")
    sub_content = content.xpath(".//div[@class='key-indicator_content offset-md-2']")
    documents = []
    for i, raw_title in enumerate(main_title):
        a_text = raw_title.xpath(".//a[1]/text()")[0]
        if a_text == 'Foreign Currency Market':
            break
    currency_rows = sub_content[i].xpath(".//tr")[1:]
    for row in currency_rows:
        cols = row.xpath(".//td")
        char_code = cols[0].xpath(".//div[@class='col-md-3 offset-md-1 _subinfo']/text()")[0]
        rate = float(cols[-1].xpath(".//text()")[0].replace(',', ''))
        documents.append([char_code, rate])

    for i, raw_title in enumerate(main_title):
        a_text = raw_title.xpath(".//a[1]/text()")[0]
        if a_text == 'Precious Metals':
            break
    metals_rows = sub_content[i].xpath(".//tr")[1:]
    for row in metals_rows:
        cols = row.xpath(".//td")
        char_code = cols[0].xpath(".//div[@class='col-md-3 offset-md-1 _subinfo']/text()")[0]
        rate = float(cols[-1].xpath(".//text()")[0].replace(',', ''))
        documents.append([char_code, rate])

    return dict(documents)
