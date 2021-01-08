#!/usr/bin/env python3
import pytest
import logging

from task_Vyazmin_Ilja_stackoverflow_analytics import (
	load_stop_words, load_questions, count_words, process_list_queries
)


QUESTIONS_TINY_STR = """
<row Id="2" PostTypeId="1" CreationDate="2019-10-14T17:28:54.933" Score="10" Title="Is SEO better better better done with repetition?" />
<row Id="23" PostTypeId="1" CreationDate="2019-10-14T17:28:54.933" Score="5" Title="What is SEO?" />
<row Id="212" PostTypeId="1" CreationDate="2020-10-14T17:28:54.933" Score="20" Title="Is Python better than Javascript?" />
<row Id="21" PostTypeId="2" CreationDate="2020-10-14T17:28:54.933" Score="20" Title="Is than Javascript?" />
"""

STOP_WORDS_TINY_STR = """
is
than
"""

QUERIES_TINY_STR = """
2019,2019,2 
2019,2020,4
"""

ANSWER_TINY_STR = """
{"start": 2019, "end": 2019, "top": [["seo", 15], ["better", 10]]}
{"start": 2019, "end": 2020, "top": [["better", 30], ["javascript", 20], ["python", 20], ["seo", 15]]}
"""

@pytest.fixture()
def tiny_stop_words_path(tmpdir):
	stop_words_path = tmpdir.join("stop_words.txt")
	stop_words_path.write(STOP_WORDS_TINY_STR)
	return stop_words_path

@pytest.fixture()
def tiny_questions_path(tmpdir):
	questions_path = tmpdir.join("questions.txt")
	questions_path.write(QUESTIONS_TINY_STR)
	return questions_path

@pytest.fixture()
def tiny_queries_path(tmpdir):
	queries_path = tmpdir.join("queries.txt")
	queries_path.write(QUERIES_TINY_STR)
	return queries_path

def test_load_stop_words(tiny_stop_words_path):
	tiny_stop_words = load_stop_words(tiny_stop_words_path)
	assert tiny_stop_words == {'is', 'than'}

def test_load_questions(tiny_questions_path):
	tiny_questions = load_questions(tiny_questions_path)
	assert type(tiny_questions) == list
	assert len(tiny_questions) == 3

def test_count_words_not_contain_stop_words(tiny_stop_words_path, tiny_questions_path):
	tiny_stop_words = load_stop_words(tiny_stop_words_path)
	tiny_questions = load_questions(tiny_questions_path)
	dict_words = count_words(tiny_questions, [1970, 2020, 10], tiny_stop_words)
	for word in dict_words:
		assert word not in tiny_stop_words

def test_process_list_queries(tiny_stop_words_path, tiny_questions_path, tiny_queries_path, capsys):
	with open(tiny_queries_path, "r") as query_fin:
		process_list_queries(
			questions_path=tiny_questions_path,
			stop_words_path=tiny_stop_words_path,
			queries_fio=query_fin
		)
	captured = capsys.readouterr()
	assert '{"start": 2019, "end": 2019, "top": [["seo", 15], ["better", 10]]}' in captured.out
	assert '{"start": 2019, "end": 2020, "top": [["better", 30], ["javascript", 20], ["python", 20], ["seo", 15]]}' in captured.out