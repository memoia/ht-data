#!/usr/bin/env python2.7

import os
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

    def __init__(self, args=None, test=False):
        self.args = args or fake_args()
        if not test:
            self.validate_args()
            self.run()

    def validate_args(self):
        if self.args.t is None or not os.path.exists(self.args.t):
            raise StandardError('Missing fixture. Use the -t flag.')

    def run(self):
        raise NotImplementedError('Implement in subclass.')


class TestDbHelper(unittest.TestCase):
    def setUp(self):
        self.obj = DbHelper(test=True)

    def test_validate_args_raises_when_missing_fixture_flag(self):
        with self.assertRaises(StandardError):
            self.obj.validate_args()

    def test_validate_args_raises_when_fixture_not_found(self):
        with self.assertRaises(StandardError):
            self.obj = DbHelper(args=fake_args(t='hello'), test=True)
            self.obj.validate_args()

    def test_validate_args_passes_otherwise(self):
        fixture = os.path.join(self.obj.fixtures, 'standard')
        self.obj = DbHelper(args=fake_args(t=fixture), test=True)
        self.obj.validate_args()

    def test_invokes_run_under_normal_circumstances(self):
        args = fake_args(t=os.path.join(self.obj.fixtures, 'standard'))
        with self.assertRaises(NotImplementedError):
            self.obj = DbHelper(args)


class DbExportHandler(DbHelper):
    def run(self):
        pass


class TestDbExportHandler(unittest.TestCase):
    pass


class DbImportHandler(DbHelper):
    def run(self):
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
