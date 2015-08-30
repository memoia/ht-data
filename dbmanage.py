#!/usr/bin/env python2.7

import os
import re
import unittest
import argparse
from StringIO import StringIO


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
        self.trans_col_delim = chr(0x1c)  # "field separator"
        self.trans_row_delim = chr(0x0b)  # "vertical tab"
        self.escape_chars = ('\\', self.trans_col_delim, self.trans_row_delim)
        if not test:
            self.validate_args()
            self.run()

    @property
    def export_path(self):
        return os.path.join(self.output,
                            'out_export_' + os.path.basename(self.fixture_path))

    @property
    def fixture_path(self):
        return self.args.t

    @property
    def col_delim(self):
        return self.args.c

    @property
    def row_delim(self):
        return self.args.r

    def validate_args(self):
        if self.args.t is None or not os.path.exists(self.args.t):
            raise StandardError('No fixture. Use the -t flag, or -h for help.')

    def run(self):
        raise NotImplementedError('Implement in subclass.')

    def encode_record(self, raw_rec):
        '''prepend \ before self.escape_chars, convert row/column delimiters'''
        for character in self.escape_chars:
            # note: this should be faster and safer than using re.
            raw_rec = raw_rec.replace(character, '\\' + character)
        return (raw_rec.replace(self.col_delim, self.trans_col_delim)
                       .replace(self.row_delim, self.trans_row_delim))

    def decode_record(self, raw_rec):
        '''remove any \ before self.escape_chars, convert delims'''
        # use lookbehind to ensure we don't split on escaped trans_col_delim
        raw_rec = self.col_delim.join(
                  re.split(r'(?<!\\)' + self.trans_col_delim, raw_rec))

        # satisfy edge case of trailing backslash prior to end of record
        # by converting end of record first.
        raw_rec = re.sub(self.trans_row_delim + '$', self.row_delim, raw_rec)

        for character in self.escape_chars:
            raw_rec = raw_rec.replace('\\' + character, character)
        return raw_rec


class TestDbHelper(unittest.TestCase):
    def setUp(self):
        self.obj = DbHelper(args=fake_args(c="\t", r="\n"), test=True)

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

    def test_encode_and_decode_return_same_string(self):
        wonky = ("\\this\tre" +         # case: starts with backslash
            self.obj.trans_col_delim +  # case: contains internal delimiters
            self.obj.trans_row_delim +
            "cord\tbacksl\\ashes\\\n")  # case: ends with backslash
        result = self.obj.decode_record(self.obj.encode_record(wonky))
        self.assertEquals(result, wonky)


class DbExportHandler(DbHelper):
    def run(self):
        buff = StringIO()
        with open(self.fixture_path, 'r') as infile:
            with open(self.export_path, 'w') as outfile:
                for character in iter(lambda: infile.read(1), ''):
                    buff.write(character)
                    # We assume that the provided record delimiter
                    # is not contained by any of the fields.
                    if character == self.row_delim:
                        outfile.write(self.encode_record(buff.getvalue()))
                        buff.close()
                        buff = StringIO()
                outfile.write(self.decode_record(buff.getvalue()))


class DbImportHandler(DbHelper):
    def run(self):
        out_path = self.export_path.replace('out_export_', 'out_import_')
        buff = StringIO()
        last = None
        with open(self.export_path, 'r') as infile:
            with open(out_path, 'w') as outfile:
                for character in iter(lambda: infile.read(1), ''):
                    buff.write(character)
                    # XXX this fails in cases where the original input
                    # has a line that ends with a backslash.
                    if last != '\\' and character == self.trans_row_delim:
                        outfile.write(self.decode_record(buff.getvalue()))
                        buff.close()
                        buff = StringIO()
                    last = character
                outfile.write(self.decode_record(buff.getvalue()))


class TestExportAndImportHandlers(unittest.TestCase):
    fixture_data = {
        'alt-col-separator': fake_args(c=',', r='\n'),
        'alt-row-separator': fake_args(c='\t', r='\r'),
        'contains-backslashes': fake_args(c='\t', r='\r'),
        'csv-with-quotes': fake_args(c=',', r='\n'),
        'standard': fake_args(c='\t', r='\r'),
        'wonky-example': fake_args(c='\t', r='\r'),
    }

    def test_export_to_import_results_in_same_as_original_fixture(self):
        failures = []
        for (ft, args) in self.fixture_data.items():
            args.t = os.path.join('fixtures', ft)
            exporter = DbExportHandler(args)
            importer = DbImportHandler(args)
            compare_to = os.path.join(importer.output, 'out_import_' + ft)
            with open(args.t, 'r') as fixture:
                with open(compare_to, 'r') as result:
                    (original, translation) = (fixture.read(), result.read())
                    if original != translation:
                        failures.append((ft, original, translation))
        self.assertEqual([], failures)


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
