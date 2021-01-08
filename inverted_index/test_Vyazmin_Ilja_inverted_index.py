from textwrap import dedent

import pytest
import logging

from task_Vyazmin_Ilja_inverted_index import (
	InvertedIndex, build_inverted_index, load_documents, load_stop_words,
	process_file_queries, process_list_queries, DEFAULT_INVERTED_INDEX_STORE_PATH,
	process_build, DEFAULT_STOP_WORDS_PATH, DEFAULT_DATASET_PATH
)

DATASET_TINY_STR = dedent("""\
	123	some words A_word and nothing
	2	some word B_word in this dataset
	5	famous_phrases to_be
	37	all words such as A_word and B_word are here
""")

STOP_WORDS_TINY = """
qwerty
snow
to_be
"""


def test_correct_equel_objects():
	index_1 = InvertedIndex({'abc': [1]})
	index_2 = InvertedIndex({'abc': [1], 'ab': [2]})
	index_3 = InvertedIndex({'abc': [1]})
	index_4 = InvertedIndex({'abc': [2], 's': [1, 2, 3]})
	assert index_1 == index_3
	assert index_1 != index_2
	assert index_2 != index_4

@pytest.fixture()
def tiny_dataset_fio(tmpdir):
	dataset_fio = tmpdir.join("dataset.txt")
	dataset_fio.write(DATASET_TINY_STR)
	return dataset_fio

@pytest.fixture()
def stop_words_fio(tmpdir):
	stop_words_fio = tmpdir.join("stop_words_tiny.txt")
	stop_words_fio.write(STOP_WORDS_TINY)
	return stop_words_fio


@pytest.fixture()
def tiny_index(tmpdir):
	tiny_index = tmpdir.join("tiny.index")
	return tiny_index


def test_can_load_documents(tiny_dataset_fio):
	documents = load_documents(tiny_dataset_fio)
	etalon_documents = {
		123: "some words A_word and nothing",
		2: "some word B_word in this dataset",
		5: "famous_phrases to_be",
		37: "all words such as A_word and B_word are here",
	}
	assert etalon_documents == documents, (
		"load_documents incorrectly loaded dataset"
	)

@pytest.mark.parametrize(
	"query, etalon_answer",
	[
		pytest.param(["A_word"], [123, 37], id="A_word"),
		pytest.param(["B_word"], [2, 37], id="B_word"),
		pytest.param(["A_word", "B_word"], [37], id="both words"),
		pytest.param(["word_does_not_exist"], [], id="word does not exist"),
		pytest.param(["to_be"], [], id="stop word")
	],
)
def test_query_inverted_index_intersect_results(tiny_dataset_fio, stop_words_fio, query, etalon_answer):
	documents = load_documents(tiny_dataset_fio)
	stop_words = load_stop_words(stop_words_fio)
	tiny_inverted_index = build_inverted_index(documents, stop_words)
	answer = tiny_inverted_index.query(query)
	assert sorted(answer) == sorted(etalon_answer), (
		f"Expected answer is {etalon_answer}, but you got {answer}"
	)

def test_can_load_wikipedia_sample():
	documents = load_documents(DEFAULT_DATASET_PATH)
	assert len(documents) == 4100, (
		"you incorrectly loaded Wikipedia sample"
	)

@pytest.fixture()
def wikipedia_documents():
	wikipedia_documents = load_documents(DEFAULT_DATASET_PATH)
	return wikipedia_documents


@pytest.fixture()
def stop_words_doc():
	stop_words_doc = load_stop_words(DEFAULT_STOP_WORDS_PATH)
	return stop_words_doc


def test_can_build_and_query_inverted_index(wikipedia_documents, stop_words_doc):
	wikipedia_inverted_index = build_inverted_index(wikipedia_documents, stop_words_doc)
	doc_ids = wikipedia_inverted_index.query(["wikipedia"])
	assert isinstance(doc_ids, list), "inverted index query should return list"


@pytest.fixture
def wikipedia_inverted_index(wikipedia_documents, stop_words_doc):
	wikipedia_inverted_index = build_inverted_index(wikipedia_documents, stop_words_doc)
	return wikipedia_inverted_index


def test_can_dump_and_load_inverted_index(tmpdir, wikipedia_inverted_index):
	index_fio = tmpdir.join("index.dump")
	wikipedia_inverted_index.dump(index_fio)
	loaded_inverted_index = InvertedIndex.load(index_fio)
	assert wikipedia_inverted_index == loaded_inverted_index, (
		"load should return the same inverted index"
	)


def test_process_build_can_load_documents(tiny_dataset_fio, stop_words_fio,  tiny_index):
	process_build(
		dataset_path=tiny_dataset_fio,
		stop_words_path=stop_words_fio,
		output=tiny_index
	)
	loaded_tiny_index = InvertedIndex.load(tiny_index)
	tiny_index_dict = {
		'some': [2, 123],
		'words': [37, 123],
		'A_word': [37, 123],
		'and': [37, 123],
		'nothing': [123],
		'word': [2],
		'B_word': [2, 37],
		'in': [2],
		'this': [2],
		'dataset': [2],
		'famous_phrases': [5],
		'all': [37],
		'such': [37],
		'as': [37],
		'are': [37],
		'here': [37]
	}
	tiny_index = InvertedIndex(tiny_index_dict)
	assert tiny_index == loaded_tiny_index, (
		"load should return the same inverted index"
	)

def test_process_file_queries_can_process_all_qutries_from_file(tiny_dataset_fio, stop_words_fio, tiny_index, capsys, caplog):
	caplog.set_level("DEBUG")
	documents = load_documents(tiny_dataset_fio)
	stop_words = load_stop_words(stop_words_fio)
	index = build_inverted_index(documents, stop_words)
	index.dump(tiny_index)
	with open("query_utf8.txt") as query_fin:
		process_file_queries(
			inverted_index_path=tiny_index,
			query_file=query_fin
		)
	captured = capsys.readouterr()
	assert captured.out == '\n\n\n'
	assert captured.err == ''

	assert any("load inverted index" in message for message in caplog.messages), (
		"There is no 'load inverted index' in logs"
	)
	assert any("['one', 'apple']" in message for message in caplog.messages), (
		"There is no ['one', 'apple'] in logs"
	)
	assert all(record.levelno <= logging.WARNING for record in caplog.records), (
		"application is unstable"
	)
	


def test_process_file_list_can_process_all_qutries_from_list(tiny_dataset_fio, stop_words_fio, tiny_index, capsys):
	documents = load_documents(tiny_dataset_fio)
	stop_words = load_stop_words(stop_words_fio)
	tiny_inverted_index = build_inverted_index(documents, stop_words)
	tiny_inverted_index.dump(tiny_index)
	ids = process_list_queries(
		inverted_index_path=tiny_index,
		query_list=[["A_word", "B_word"]]
	)
	assert ids == '37'