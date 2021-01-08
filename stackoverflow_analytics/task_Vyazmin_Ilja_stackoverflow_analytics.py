#!/usr/bin/env python3
"""Module for search most popular topics at stackoverflow"""
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from collections import Counter
import logging
import logging.config
import json
import re

import yaml
from lxml import etree

APPLICATION_NAME = "stackoverflow_analytics"
DEFAULT_QUESTIONS_PATH = "./stackoverflow_posts_sample.xml"
DEFAULT_STOP_WORDS_PATH = "./stop_words_en.txt"
DEFAULT_LOGGING_CONFIG_FILE_PATH = "logging.conf.yml"


logger = logging.getLogger(APPLICATION_NAME)


def load_questions(questions_path):
    """Load and prepare information about stackoverflow questions"""
    questions = []
    with open(questions_path, "r", encoding="utf-8") as questions_fio:
        for line in questions_fio:
            try:
                root = etree.XML(line)
                post_type = int(root.attrib['PostTypeId'])
                if post_type != 1:
                    continue
                question_dict = dict()
                question_dict['CreationDate'] = root.attrib['CreationDate']
                question_dict['Title'] = root.attrib['Title']
                question_dict['Score'] = root.attrib['Score']
                questions.append(question_dict)
            except BaseException:
                continue
    return questions


def load_stop_words(stop_words_path):
    """Load file with stop words"""
    stop_words = set()
    with open(stop_words_path, "r", encoding="koi8-r") as stop_words_fio:
        for line in stop_words_fio:
            word = line.rstrip()
            if len(word) > 0:
                stop_words.add(word)
    return stop_words


def count_words(questions, query, stop_words):
    """Create dict of count words from questions by query"""
    dict_words = Counter()
    for question_dict in questions:
        year = int(question_dict['CreationDate'][:4])
        if year < query[0] or year > query[1]:
            continue
        text = set(re.findall(r"\w+", question_dict['Title'].lower())) - stop_words
        for word in text:
            dict_words[word] += int(question_dict['Score'])
    return dict_words


def process_list_queries(questions_path, stop_words_path, queries_fio):
    """Contains using inverted index functionality for queries from comand string"""
    questions = load_questions(questions_path)
    stop_words = load_stop_words(stop_words_path)
    logger.info("process XML dataset, ready to serve queries")
    for query in queries_fio:
        if len(query) <= 1:
            continue
        logger.debug('got query "%s"', query.rstrip())
        query = list(map(int, query.rstrip().split(',')))
        dict_words = count_words(questions, query, stop_words)
        top_count = int(query[2])
        dict_len = len(dict_words)
        if dict_len < top_count:
            logger.warning('not enough data to answer, found %d words out of %d for period "%d,%d"',
                            dict_len, top_count, query[0], query[1])
            top_count = dict_len
        top_list = sorted(dict_words.items(), key=lambda x: (-x[1], x[0]))[:top_count]
        answer = dict()
        answer["start"] = int(query[0])
        answer["end"] = int(query[1])
        answer["top"] = top_list
        answer_json = json.dumps(answer)
        print(answer_json)
    logger.info("finish processing queries")


def setup_parser(parser):
    """Sets up subparesers and keywords for CLI"""
    parser.add_argument(
        "--questions", required=False, dest='questions',
        default=DEFAULT_QUESTIONS_PATH,
        help="path to questions to load",
    )
    parser.add_argument(
        "--stop-words", required=False, dest='stop_words',
        default=DEFAULT_STOP_WORDS_PATH,
        help="path to stop-words to load",
    )
    parser.add_argument(
        "--queries", required=True, dest='queries', type=FileType("r"),
        help="path to queries to load",
    )

def setup_logging():
    """Sets up logging for CLI"""
    with open(DEFAULT_LOGGING_CONFIG_FILE_PATH) as config_fin:
        config = yaml.safe_load(config_fin)
        logging.config.dictConfig(config)


def main():
    """Distributes work between functions"""
    parser = ArgumentParser(
        prog="stackoverflow-analytics",
        description="tool to search most popular topics at stackoverflow",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    setup_logging()
    process_list_queries(arguments.questions, arguments.stop_words, arguments.queries)

if __name__ == "__main__":
    main()
