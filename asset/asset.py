#!/usr/bin/env python3
from argparse import ArgumentParser, FileType
from abc import ABC, abstractmethod
import sys
import logging
import time
from time import sleep
from collections import namedtuple

import cbr

logger = logging.getLogger("asset")

DEFAULT_SMALL_SLEEP_TIME = 1
DEFAULT_BIG_SLEEP_TIME = 2


def do_busy_work(sleep_time=DEFAULT_SMALL_SLEEP_TIME):
    time.sleep(sleep_time)


def do_busy_work_with_full_import(sleep_time=DEFAULT_BIG_SLEEP_TIME):
    sleep(sleep_time)


def do_busy_work_with_nested_calls():
    do_busy_work()
    do_busy_work_with_full_import()


class Asset(ABC):
    def __init__(self, name: str, capital: float, interest: float):
        self.name = name
        self.capital = capital
        self.interest = interest

    def calculate_revenue(self, years: int, forecast_strategy=None) -> float:
        revenue_in_usd = self.capital * ((1.0 + self.interest) ** years - 1.0)
        forecast_strategy = forecast_strategy or DefaultForecastStrategy()
        revenue = forecast_strategy.fixup_revenue_prediction(revenue)
        revenue *= (1.0 - self.calculate_tax(revenue))
        return revenue

    @abstractmethod
    def calculate_tax(self, revenue):
        raise NotImplementedError

    @classmethod
    def build_from_str(cls, raw: str):
        logger.debug("building asset object...")
        #do_busy_work_with_nested_calls()
        name, capital, interest = raw.strip().split()
        capital = float(capital)
        interest = float(interest)
        asset = cls(name=name, capital=capital, interest=interest)
        return asset

    def __repr__(self):
        repr_ = f"""{self.__class__.__name__}({self.name}, {self.capital}, {self.interest})"""
        return repr_


class RuAsset(Asset):
    def calculate_tax(self, revenue):
        return 0.13


class IEAsset(Asset):
    def calculate_tax(self, revenue):
        if revenue > 1000:
            return 0.3
        return 0.2


AssetFactory = namedtuple("AssetFactory", ["create_asset"])
ru_factory = AssetFactory(create_asset=RuAsset)
ie_factory = AssetFactory(create_asset=IEAsset)


class ForecastStrategy(ABC):
    @abstractmethod
    def fixup_revenue_prediction(self, revenue):
        raise NotImplementedError


class DefaultForecastStrategy(ForecastStrategy):
    def fixup_revenue_prediction(self, revenue):
        return revenue


class PessimisticForecastStrategy(ForecastStrategy):
    def fixup_revenue_prediction(self, revenue):
        return 0.9 * revenue


class OptimisticForecastStrategy(ForecastStrategy):
    def fixup_revenue_prediction(self, revenue):
        return revenue / 0.9


# class AssetFactory(ABC):
#     @abstractmethod
#     def create_asset(self, name, capital, interest):
#         raise NotImplementedError


# class RUFactory(ABC):
#     @abstractmethod
#     def create_asset(self, name, capital, interest):
#         asset = RUAsset(name, capital, interest)
#         return asset


# class IEFactory(ABC):
#     @abstractmethod
#     def create_asset(self, name, capital, interest):
#         asset = IEAsset(name, capital, interest)
#         return asset


class Bank:
    def __init__(self, factory, forecast_strategy=None):
        self._factory = factory
        self._forecast_strategy = forecast_strategy or DefaultForecastStrategy()
        self._asset_collection = {}

    def add_asset(self, name, capital, interest):
        asset = self._factory.creare_asset(name, capital, interest)
        self._asset_collection[asset.name] = asset

    def set_forecast_strategy(self, forecast_strategy):
        self._forecast_strategy = forecast_strategy

    def calculate_revenue(self, year):
        total_revenue = 0.0
        for asset_name, asset in self._asset_collection.items():
            asset_revenue = asset.calculate_revenue(year, self._forecast_strategy)
            total_revenue += asset_revenue
        return total_revenue

    def print_report(self, years):
        print("Asset library")
        for assert_index, asset_name in enumerate(self._asset_collection):
            asset = self._asset_collection[asset_name]
            print(f"{asset_index}. {asset.name} with capital {asset.capital} and interest rate {asset.interest}")
        print("Expected revenue")
        for year in years:
            expected_revenue = self.calculate_revenue(year)
            print(f"{year:5}: {expected_revenue:10.3f}")


def load_asset_from_file(fileio):
    logger.info("reading asset file...")
    raw = fileio.read()
    asset = Asset.build_from_str(raw)
    return asset


def process_cli_arguments(arguments):
    print_asset_revenue(arguments.asset_fin, arguments.periods)


def print_asset_revenue(asset_fin, periods):
    asset = load_asset_from_file(asset_fin)
    for period in periods:
        revenue = asset.calculate_revenue(period)
        logger.debug("asset %s for period %s gives %s", asset, period, revenue)
        print(f"{period:5}: {revenue}")
        # consider nice formatting:
        # print(f"{period:5}: {revenue:10.3f}")


def setup_parser(parser):
    parser.add_argument("-f", "--filepath", dest="asset_fin", default=sys.stdin, type=FileType("r"))
    parser.add_argument("-p", "--periods", nargs="+", type=int, metavar="YEARS", required=True)
    parser.set_defaults(callback=process_cli_arguments)


def main():
    parser = ArgumentParser(
        prog="asset",
        description="tool to forecast asset revenue",
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()
