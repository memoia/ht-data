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
        self.escape_sometimes = (self.col_delim, self.row_delim)
        self.escape_always = ('\\', self.trans_col_delim, self.trans_row_delim)
        self.escape_chars = self.escape_always + self.escape_sometimes
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
        buff = StringIO()
        escape_delimiters = False
        for character in raw_rec:
            if character == '"':
                escape_delimiters = not escape_delimiters
            elif character in self.escape_always or (
                    escape_delimiters and character in self.escape_sometimes):
                buff.write('\\')
            else:
                character = (character
                    .replace(self.col_delim, self.trans_col_delim)
                    .replace(self.row_delim, self.trans_row_delim))
            buff.write(character)
        return buff.getvalue()

    def decode_record(self, raw_rec):
        '''remove any \ before self.escape_chars, convert delims'''
        if not raw_rec:
            return raw_rec

        # use lookbehind to ensure we don't split on escaped trans_col_delim
        raw_rec = self.col_delim.join(
                  re.split(r'(?<!\\)' + self.trans_col_delim, raw_rec))

        # satisfy edge case of trailing backslash prior to end of record
        # by converting end of record first.
        raw_rec = re.sub(self.trans_row_delim + '$', self.row_delim, raw_rec)

        for character in self.escape_chars:
            raw_rec = raw_rec[:-1].replace('\\' + character, character) + raw_rec[-1]
        return raw_rec

    def encode_each_record(self, fd):
        buff = StringIO()
        for character in iter(lambda: fd.read(1), ''):
            buff.write(character)
            if character == self.row_delim:
                yield self.encode_record(buff.getvalue())
                buff.close()
                buff = StringIO()
        yield self.encode_record(buff.getvalue())


class TestDbHelper(unittest.TestCase):

    def setUp(self):
        self.obj = DbHelper(args=fake_args(c="\t", r="\n"), test=True)
        self.wonky_string = ("\\this\tre" +  # case: starts with backslash
            self.obj.trans_col_delim +       # case: contains internal delims
            self.obj.trans_row_delim +
            "cord\tbacksl\\ashes\\\n")       # case: ends with backslash

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

    def test_encode_escapes_backslashes_and_delimiters(self):
        expected = '\\\\this\x1cre\\\x1c\\\x0bcord\x1cbacksl\\\\ashes\\\\\x0b'
        self.assertEquals(expected, self.obj.encode_record(self.wonky_string))

    def test_encode_escapes_delimiters_within_row(self):
        self.obj = DbHelper(args=fake_args(c=',', r="\n"), test=True)
        row = 'a,"b, c",d\n'  # (a, "b, c", d)
        self.assertEqual('a\x1c"b\\, c"\x1cd\x0b', self.obj.encode_record(row))

    def test_encode_and_decode_return_same_string(self):
        result = self.obj.decode_record(self.obj.encode_record(self.wonky_string))
        self.assertEquals(result, self.wonky_string)

    def test_encode_each_record_separates_rows(self):
        fake_file = StringIO(self.wonky_string + 'another\trecord\nand\tmore')
        self.assertEqual(3, len(list(self.obj.encode_each_record(fake_file))))


class DbExportHandler(DbHelper):
    def run(self):
        with open(self.fixture_path, 'r') as infile:
            with open(self.export_path, 'w') as outfile:
                for rec in self.encode_each_record(infile):
                    outfile.write(rec)


class DbImportHandler(DbHelper):
    def run(self):
        out_path = self.export_path.replace('out_export_', 'out_import_')
        buff = StringIO()
        last = None
        with open(self.export_path, 'r') as infile:
            with open(out_path, 'w') as outfile:
                for character in iter(lambda: infile.read(1), ''):
                    buff.write(character)
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
        'empty-file': fake_args(c='\t', r='\r'),
        'empty-file-with-newline': fake_args(c='\t', r='\r'),
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
