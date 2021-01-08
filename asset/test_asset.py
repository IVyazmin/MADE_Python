import pytest
import logging
from argparse import Namespace
from unittest.mock import call, patch, MagicMock

from asset import process_cli_arguments, DEFAULT_SMALL_SLEEP_TIME, DEFAULT_BIG_SLEEP_TIME, Asset


@patch("asset.load_asset_from_file")
def test_process_arguments_call_load_once(mock_load_asset_from_file):
	with open("asset_example.txt") as fin:
		arguments = Namespace(
			asset_fin=fin,
			periods=[1, 2, 5],
		)
		print(mock_load_asset_from_file.__format__)
		process_cli_arguments(arguments)

		print(mock_load_asset_from_file.calls)
		expected_calls = [
			call(fin),
			call().calculate_revenue(1),
			call().calculate_revenue(2),
			call().calculate_revenue(5),
		]
		mock_load_asset_from_file.assert_called_once_with(fin)
		mock_load_asset_from_file.assert_has_calls(expected_calls, any_order=True)
		mock_load_asset_from_file.return_value.calculate_revenue.call_args_list == [call(1), call(2), call(5)]


@patch("asset.sleep")
@patch("time.sleep")
def _test_can_mock_time_sleep(mock_time_sleep, mock_asset_sleep):
	with open("asset_example.txt") as fin:
		arguments = Namespace(
			asset_fin=fin,
			periods=[1, 2, 5],
		)
		process_cli_arguments(arguments)
		mock_time_sleep.assert_called_once_with(DEFAULT_SMALL_SLEEP_TIME)
		mock_asset_sleep.assert_called_once_with(DEFAULT_BIG_SLEEP_TIME)


@patch("asset.Asset")
def test_asset_calculate_revenue_always_return_100500(mock_asset_class, capsys):
	#mock_asset_class = MagicMock(spec=Asset)
	mock_asset_class.calculate_revenue.return_value = 100500.0
	mock_asset_class.build_from_str.return_value = mock_asset_class
	with open("asset_example.txt") as fin:
		arguments = Namespace(
			asset_fin=fin,
			periods=[1, 2, 5],
		)
		process_cli_arguments(arguments)

		captured = capsys.readouterr()
		for line in captured.out.splitlines():
			assert "100500" in line, "..."


@patch("cbr.get_usd_course")
def test_can_mock_external_calls(mock_get_usd_course):
	start_course = 75.0
	def increase_course():
		nonlocal start_course
		start_course += 1.5
		return start_course
	mock_get_usd_course.side_effect = increase_course
	with open("asset_example.txt") as fin:
		arguments = Namespace(
			asset_fin=fin,
			periods=[1, 1, 1, 1, 1],
		)
		process_cli_arguments(arguments)


@patch("asset.load_asset_from_file")
def test_can_mock_load_and_returned_class(mock_load_asset_from_file, capsys):
	mock_asset_class = MagicMock()
	mock_asset_class.calculate_revenue.return_value = 100500.0
	mock_load_asset_from_file.return_value = mock_asset_class
	with open("asset_example.txt") as fin:
		arguments = Namespace(
			asset_fin=fin,
			periods=[1, 2, 5],
		)
		process_cli_arguments(arguments)

		captured = capsys.readouterr()
		for line in captured.out.splitlines():
			assert "100500" in line, "..."