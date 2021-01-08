#!/usr/bin/env python3
"""Module for work with inverted index"""
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType, ArgumentTypeError
from collections import defaultdict
from io import TextIOWrapper
import struct
import logging
import logging.config

import yaml

APPLICATION_NAME = "inverted_index"
DEFAULT_DATASET_PATH = "./wikipedia_sample"
DEFAULT_INVERTED_INDEX_STORE_PATH = "inverted.index"
DEFAULT_STOP_WORDS_PATH = "./stop_words_en.txt"
DEFAULT_LOGGING_CONFIG_FILE_PATH = "logging.conf.yml"


logger = logging.getLogger(APPLICATION_NAME)


class EncodedFileType(FileType):
    """FileType with using encoding"""
    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                stdin = TextIOWrapper(sys.stdin.buffer, encoding=self._encoding)
                return stdin
            if 'w' in self._mode:
                stdout = TextIOWrapper(sys.stdout.buffer, encoding=self._encoding)
                return stdout
            msg = 'argument "-" with mode %r' % self._mode
            raise ValueError(msg)

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding, self._errors)
        except OSError as exception:
            message = "can't open '%s': %s"
            raise ArgumentTypeError(message % (string, exception)) from exception



class InvertedIndex:
    """Class for work with inverted index"""
    def __init__(self, dict_index=None):
        self.dict_index = dict_index

    def __eq__(self, another):
        for key in self.dict_index:
            another_value = another.dict_index.get(key, [])
            self_value = self.dict_index[key]
            if sorted(self_value) != sorted(another_value):
                return False
        if len(self.dict_index) != len(another.dict_index):
            return False
        return True

    def query(self, words: list) -> list:
        """Return the list of relevant documents for the given query"""
        assert isinstance(words, list), (
            "query should be provided with a list of words"
        )
        logger.debug("query inverted index with request %s", repr(words))
        response = set(self.dict_index.get(words[0], set()))
        words.pop(0)
        for word in words:
            next_doc = set(self.dict_index.get(word, set()))
            response = response & next_doc
        return list(response)


    def dump(self, filepath: str):
        """Save inverted index in binary format into hard drive"""
        dict_index_small = dict()
        dict_index_large = dict()
        for key in self.dict_index:
            if len(self.dict_index[key]) < 255:
                dict_index_small[key] = self.dict_index[key]
            else:
                dict_index_large[key] = self.dict_index[key]
        with open(filepath, 'wb') as dump_file:
            dict_len = len(dict_index_small)
            dict_len_pack = struct.pack('>i', dict_len)
            dump_file.write(dict_len_pack)

            for key in dict_index_small:
                key_bin = key.encode()
                key_len = len(key_bin)
                key_len_pack = struct.pack('>B', key_len)
                dump_file.write(key_len_pack)
                key_pack = struct.pack('>' + str(key_len) + 's', key_bin)
                dump_file.write(key_pack)

                values = dict_index_small[key]
                list_len = len(values)
                list_len_pack = struct.pack('>B', list_len)
                dump_file.write(list_len_pack)
                values_pack = struct.pack('>' + str(list_len) + 'H', *values)
                dump_file.write(values_pack)

            dict_len = len(dict_index_large)
            dict_len_pack = struct.pack('>i', dict_len)
            dump_file.write(dict_len_pack)

            for key in dict_index_large:
                key_bin = key.encode()
                key_len = len(key_bin)
                key_len_pack = struct.pack('>B', key_len)
                dump_file.write(key_len_pack)
                key_pack = struct.pack('>' + str(key_len) + 's', key_bin)
                dump_file.write(key_pack)

                values = dict_index_large[key]
                list_len = len(values)
                list_len_pack = struct.pack('>H', list_len)
                dump_file.write(list_len_pack)
                values_pack = struct.pack('>' + str(list_len) + 'H', *values)
                dump_file.write(values_pack)


    @classmethod
    def load(cls, filepath: str):
        """Load inverted from binary file"""
        logger.info("load inverted index %s", filepath)
        with open(filepath, 'rb') as load_file:
            dict_len = load_file.read(4)
            dict_len = struct.unpack('>i', dict_len)[0]
            dict_index = dict()
            for _ in range(dict_len):
                key_len = load_file.read(1)
                key_len = struct.unpack('>B', key_len)[0]
                pack_format = '>' + str(key_len) + 's'
                key = load_file.read(key_len)
                key = struct.unpack(pack_format, key)[0]
                key = key.decode()

                list_len = load_file.read(1)
                list_len = struct.unpack('>B', list_len)[0]
                values = load_file.read(list_len * 2)
                pack_format = '>' + str(list_len) + 'H'
                values = struct.unpack(pack_format, values)
                values = list(values)
                dict_index[key] = values

            dict_len = load_file.read(4)
            dict_len = struct.unpack('>i', dict_len)[0]
            for _ in range(dict_len):
                key_len = load_file.read(1)
                key_len = struct.unpack('>B', key_len)[0]
                pack_format = '>' + str(key_len) + 's'
                key = load_file.read(key_len)
                key = struct.unpack(pack_format, key)[0]
                key = key.decode()

                list_len = load_file.read(2)
                list_len = struct.unpack('>H', list_len)[0]
                values = load_file.read(list_len * 2)
                pack_format = '>' + str(list_len) + 'H'
                values = struct.unpack(pack_format, values)
                values = list(values)
                dict_index[key] = values
            inverted_index = cls(dict_index)
        return inverted_index



def load_documents(filepath: str):
    """Load file with documents and put into dictionary"""
    logger.info("loading documents to build inverted index")
    documents = dict()
    with open(filepath, 'r') as doc_file:
        for line in doc_file:
            line = line.rstrip()
            idx, line = line.split(maxsplit=1)
            documents[int(idx)] = line.rstrip()
    return documents


def load_stop_words(stop_words_path):
    """Load file with stop words"""
    logger.info("loading stop words")
    stop_words = set()
    with open(stop_words_path, 'r') as stop_words_file:
        for line in stop_words_file:
            word = line.rstrip()
            stop_words.add(word)
    return stop_words


def build_inverted_index(documents, stop_words):
    """Take list of documents and return inverted index"""
    logger.info("building inverted index for provided documents")
    dict_index = defaultdict(list)
    for idx in documents:
        document = documents[idx].split()
        document = set(document) - stop_words
        for word in document:
            dict_index[word].append(idx)

    inverted_index = InvertedIndex()
    inverted_index.dict_index = dict_index
    return inverted_index


def callback_build(arguments):
    """Callback for build mod"""
    return process_build(arguments.dataset_path, arguments.stop_words, arguments.output)


def process_build(dataset_path, stop_words_path, output):
    """Contains building inverted index functionality"""
    logger.debug("call build with: %s and %s", dataset_path, output)
    documents = load_documents(dataset_path)
    stop_words = load_stop_words(stop_words_path)
    inverted_index = build_inverted_index(documents, stop_words)
    inverted_index.dump(output)
    return inverted_index


def callback_query(arguments):
    """Callback for query mod"""
    if arguments.query_list is not None:
        process_list_queries(arguments.inverted_index_path, arguments.query_list)
    else:
        process_file_queries(arguments.inverted_index_path, arguments.query_file)


def process_file_queries(inverted_index_path, query_file):
    """Contains using inverted index functionality for queries from file"""
    inverted_index = InvertedIndex.load(inverted_index_path)
    for query in query_file:
        query = query.strip()
        query = query.split()
        document_ids = inverted_index.query(query)
        document_ids = [str(x) for x in document_ids]
        document_ids = ",".join(document_ids)
        print(document_ids)
    return document_ids


def process_list_queries(inverted_index_path, query_list):
    """Contains using inverted index functionality for queries from comand string"""
    inverted_index = InvertedIndex.load(inverted_index_path)
    for query in query_list:
        document_ids = inverted_index.query(query)
        document_ids = [str(x) for x in document_ids]
        document_ids = ",".join(document_ids)
        print(document_ids)
    return document_ids


def setup_parser(parser):
    """Sets up subparesers and keywords for CLI"""
    subparsers = parser.add_subparsers(help="choose comand")

    build_parser = subparsers.add_parser(
        "build",
        help="build inverted index and save in binary format into hard drive",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    build_parser.add_argument(
        "-d", "--dataset", dest='dataset_path', required=False,
        default=DEFAULT_DATASET_PATH,
        help="path to dataset to load",
    )
    build_parser.add_argument(
        "-o", "--output", required=False,
        default=DEFAULT_INVERTED_INDEX_STORE_PATH,
        help="path to store inverted index",
    )
    build_parser.add_argument(
        "-s", "--stop-words", dest='stop_words', required=False,
        default=DEFAULT_STOP_WORDS_PATH,
        help="path to stop words",
    )
    build_parser.add_argument(
        "-v", "--verbocity", dest='verbocity', required=False,
        default=0, action='count',
        help="choose verbocity level",
    )
    build_parser.set_defaults(callback=callback_build)

    query_parser = subparsers.add_parser(
        "query", help="query inverted index",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    query_parser.add_argument(
        "-i", "--index", required=False,
        dest="inverted_index_path",
        default=DEFAULT_INVERTED_INDEX_STORE_PATH,
        help="path to read inverted index",
    )
    query_parser.add_argument(
        "--query", required=False, dest="query_list", action="append", nargs="+",
        help="query string",
    )
    query_file_group = query_parser.add_mutually_exclusive_group(required=False)
    query_file_group.add_argument(
        "--query-file-utf8", dest="query_file", type=EncodedFileType("r", encoding="utf-8"),
        default=TextIOWrapper(sys.stdin.buffer, encoding="utf-8"),
        help="query to run against inverted index",
    )
    query_file_group.add_argument(
        "--query-file-cp1251", dest="query_file", type=EncodedFileType("r", encoding="cp1251"),
        default=TextIOWrapper(sys.stdin.buffer, encoding="cp1251"),
        help="query to run against inverted index",
    )
    query_parser.add_argument(
        "-v", "--verbocity", dest='verbocity', required=False,
        default=0, action='count',
        help="choose verbocity level",
    )
    query_parser.set_defaults(callback=callback_query)

def setup_logging(arguments):
    """Sets up logging for CLI"""
    verbocity_dict = {
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG
    }
    with open(DEFAULT_LOGGING_CONFIG_FILE_PATH) as config_fin:
        config = yaml.safe_load(config_fin)
        if arguments.verbocity in (1, 2, 3):
            config['handlers']['stream_handler']['level'] = verbocity_dict[arguments.verbocity]
        else:
            config['loggers']['inverted_index']['propagate'] = False
        logging.config.dictConfig(config)

def main():
    """Distributes work between functions"""
    parser = ArgumentParser(
        prog="inverted-index",
        description="tool to build, dump, load and query inverted index",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    setup_logging(arguments)
    logger.debug(arguments)

    arguments.callback(arguments)

if __name__ == "__main__":
    main()
