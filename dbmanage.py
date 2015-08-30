#!/usr/bin/env python2.7

import os
import csv
import unittest
import argparse


HERE = os.path.dirname(os.path.abspath(__file__))


def fake_args(**kwargs):
    map(lambda k: kwargs.setdefault(k, None), ['t', 'c', 'r'])
    args = lambda: None
    for k, v in kwargs.items():
        setattr(args, k, v)
    return args


class DbHelper(object):
    fixtures = os.path.join(HERE, 'fixtures')
    output = os.path.join(HERE, 'output')
    args = fake_args()

    def validate_args(self):
        if self.args.t is None or not os.path.exists(self.args.t):
            raise StandardError('Missing fixture. Use the -t flag.')


class DbExportHandler(DbHelper):
    pass


class TestDbExportHandler(unittest.TestCase):
    pass


class DbImportHandler(DbHelper):
    pass


class TestDbImportHandler(unittest.TestCase):
    pass


class InvokeTestsHandler(object):
    def __init__(self, _):
        unittest.main()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', action='store', type=str,
                        metavar='<fixture-name>',
                        help='name of related fixture')
    parser.add_argument('-c', action='store', type=str,
                        metavar='<col-delimiter>',
                        default="\t",
                        help='character delimiting fields (default: tab)')
    parser.add_argument('-r', action='store', type=str,
                        metavar='<row-delimiter>',
                        default="\n",
                        help='character delimiting records (default: newline)')
    args = parser.parse_args()
    handler = {
        'dbimport': DbImportHandler,
        'dbexport': DbExportHandler,
    }
    handler.get(parser.prog, InvokeTestsHandler)(args)


if __name__ == '__main__':
    main()
