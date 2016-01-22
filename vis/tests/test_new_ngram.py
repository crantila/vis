#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               analyzers_tests/test_ngram.py
# Purpose:                Test the NGram Indexer
#
# Copyright (C) 2013, 2014 Christopher Antila, Alexander Morgan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
"""Tests for the NGramIndexer and its helper functions."""

# pylint: disable=too-many-public-methods

import os
import unittest
import pandas
from vis.analyzers.indexers import new_ngram
import pdb
# find pathname of the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]

VERTICAL_TUPLES = [(0.0, 'P4'), (4.0, 'M3'), (8.0, 'M6'), (12.0, 'P8'), (14.0, 'm6'), (16.0, 'm7'),
                   (18.0, 'M6'), (20.0, 'M6'), (22.0, 'P5'), (28.0, 'P4'), (31.0, 'A4'), (32.0, 'P4'),
                   (34.0, 'm3'), (36.0, 'Rest'), (38.0, 'Rest')]
VERT_DF = pandas.read_pickle(os.path.join(VIS_PATH, 'tests', 'expecteds', 'new_ngram_1.pickle'))

HORIZONTAL_TUPLES = [(0.0, 'P4'), (4.0, '-m3'), (8.0, '-M2'), (12.0, 'M3'), (14.0, '-M2'),
                     (16.0, '-M2'), (20.0, 'P5'), (28.0, '-M2'), (31.0, '-m2'), (32.0, 'Rest')]
HORIZ_DF = pandas.read_pickle(os.path.join(VIS_PATH, 'tests', 'expecteds', 'new_ngram_2.pickle'))

EXPECTED = [(0.0, '[P4] (P4) [M3] (-m3) [M6] (-M2) [P8]'),
            (4.0, '[M3] (-m3) [M6] (-M2) [P8] (M3) [m6]'),
            (8.0, '[M6] (-M2) [P8] (M3) [m6] (-M2) [m7]'),
            (12.0, '[P8] (M3) [m6] (-M2) [m7] (-M2) [M6]'),
            (14.0, '[m6] (-M2) [m7] (-M2) [M6] (P1) [M6]'),
            (16.0, '[m7] (-M2) [M6] (P1) [M6] (P5) [P5]'),
            (18.0, '[M6] (P1) [M6] (P5) [P5] (P1) [P8]'),
            (20.0, '[M6] (P5) [P5] (P1) [P8] (P1) [P4]'),
            (22.0, '[P5] (P1) [P8] (P1) [P4] (-M2) [M3]'),
            (26.0, '[P8] (P1) [P4] (-M2) [M3] (P1) [A4]'),
            (28.0, '[P4] (-M2) [M3] (P1) [A4] (-m2) [P4]'),
            (30.0, '[M3] (P1) [A4] (-m2) [P4] (Rest) [m3]')]
EXPECTED_DF = pandas.read_pickle(os.path.join(VIS_PATH, 'tests', 'expecteds', 'new_ngram_3.pickle'))

# iterables = [['interval.HorizontalIntervalIndexer'], ('1',)]
# hmi = pandas.MultiIndex.from_product(iterables, names = ['Indexer', 'Parts'])
# HORIZ_DF.columns = hmi

# iterables = [['new_ngram.NewNGramIndexer'], ('0,1: 1',)]
# emi = pandas.MultiIndex.from_product(iterables, names = ['Indexer', 'Parts'])
# EXPECTED_DF.columns = emi


# pdb.set_trace()


# VERT_DATA.to_pickle('/home/amor/Code/vis-framework/vis/tests/expecteds/new_ngram_1.pickle')
# HORIZ_DF.to_pickle('/home/amor/Code/vis-framework/vis/tests/expecteds/new_ngram_2.pickle')
# EXPECTED_DF.to_pickle('/home/amor/Code/vis-framework/vis/tests/expecteds/new_ngram_3.pickle')

# pdb.set_trace()

def series_maker(lotuples):
    """Turn a List Of TUPLES (offset, 'value') into a Series."""
    return pandas.Series([x[1] for x in lotuples], index=[x[0] for x in lotuples])


class TestNewNGramIndexer(unittest.TestCase):
    """Tests for the NewNGramIndexer and its helper functions."""

    def test_init_1(self):
        """that __init__() works properly (only required settings given)"""
        # pylint: disable=protected-access
        setts = {'n': 1, 'vertical': ['0,1']}
        actual = new_ngram.NewNGramIndexer((VERT_DF,), setts)
        for setting in ('n', 'vertical'):
            self.assertEqual(setts[setting], actual._settings[setting])
        for setting in ('horizontal', 'use brackets', 'terminator', 'continuer'):
            self.assertEqual(new_ngram.NewNGramIndexer.default_settings[setting], actual._settings[setting])

    def test_init_2(self):
        """that __init__() works properly (all settings given)"""
        # pylint: disable=protected-access
        setts = {'n': 1, 'vertical': ['0,1'], 'horizontal': 'banana', 'use brackets': True,
                 'terminator': 'RoboCop', 'continuer': 'Alex Murphy', 'hanging': True}
        actual = new_ngram.NewNGramIndexer((VERT_DF, HORIZ_DF), setts)
        for setting in ('n', 'vertical', 'horizontal', 'use brackets', 'terminator', 'continuer', 'hanging'):
            self.assertEqual(setts[setting], actual._settings[setting])

    def test_init_3(self):
        """that __init__() fails when 'n' is too short"""
        # pylint: disable=protected-access
        setts = {'n': 0, 'vertical': ['0,1']}  # n is too short
        self.assertRaises(RuntimeError, new_ngram.NewNGramIndexer, (VERT_DF,), setts)
        try:
            new_ngram.NewNGramIndexer((VERT_DF,), setts)
        except RuntimeError as run_err:
            self.assertEqual(new_ngram.NewNGramIndexer._N_VALUE_TOO_LOW, run_err.args[0])

    def test_init_4(self):
        """that __init__() fails when there are no 'vertical' events"""
        # pylint: disable=protected-access
        setts = {'n': 14, 'horizontal': [0]}  # no "vertical" parts
        self.assertRaises(RuntimeError, new_ngram.NewNGramIndexer, 'a DataFrame', setts)
        try:
            new_ngram.NewNGramIndexer('a DataFrame', setts)
        except RuntimeError as run_err:
            self.assertEqual(new_ngram.NewNGramIndexer._MISSING_SETTINGS, run_err.args[0])

    def test_ngram_1a(self):
        """most basic test"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A a B', 'B b C', 'C c D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_1b(self):
        """like test _1a but with an extra element in "scores" and no "horizontal" assignment"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal = pandas.Series(['a', 'b', 'c'], index=[1, 2, 3])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'vertical': [('vert', '0,1')], 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A B', 'B C', 'C D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_1c(self):
        """like test _1a but with 'mark singles' instead of 'use brackets'"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'mark singles': False}
        expected = pandas.DataFrame([pandas.Series(['A a B', 'B b C', 'C c D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_2(self):
        """adds the grouping characters"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'use brackets': True}
        expected = pandas.DataFrame([pandas.Series(['[A] (a) [B]', '[B] (b) [C]', '[C] (c) [D]'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1] (1)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_3(self):
        """test _1 but n=3"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 3, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A a B b C', 'B b C c D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_4(self):
        """test _1 but with two verticals"""
        vertical_a = pandas.Series(['A', 'B', 'C', 'D'])
        vertical_b = pandas.Series(['Z', 'X', 'Y', 'W'])
        horizontal = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical_a, vertical_b, horizontal],
                                  index=[['vert', 'vert', 'horiz'], ['0,1', '0,2', '2']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '2')], 'vertical': [('vert', '0,1'), ('vert', '0,2')],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['[A Z] a [B X]', '[B X] b [C Y]', '[C Y] c [D W]'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1 0,2] 2']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_5(self):
        """test _0 but with two horizontals, and the order of 'horizontal' setting is important"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal_b = pandas.Series(['z', 'x', 'y'])
        horizontal_a = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical, horizontal_b, horizontal_a],
                                  index=[['vert', 'horiz', 'horiz'], ['0,1', '2', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1'), ('horiz', '2')], 'vertical': [('vert', '0,1')],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A (a z) B', 'B (b x) C', 'C (c y) D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 (1 2)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_6(self):
        """combination of tests _3 and _4"""
        vertical_a = pandas.Series(['A', 'B', 'C', 'D'])
        vertical_b = pandas.Series(['Z', 'X', 'Y', 'W'])
        horizontal_a = pandas.Series(['a', 'b', 'c'])
        horizontal_b = pandas.Series(['z', 'x', 'y'])
        in_val = pandas.DataFrame([vertical_a, vertical_b, horizontal_a, horizontal_b],
                                  index=[['vert', 'vert', 'horiz', 'horiz'],
                                         ['0,1', '0,2', '1', '2']]).T
        setts = {'n': 2, 'use brackets': False,
                 'horizontal': [('horiz', '1'), ('horiz', '2')],
                 'vertical': [('vert', '0,1'), ('vert', '0,2')]}
        expected = pandas.DataFrame([pandas.Series(['[A Z] (a z) [B X]',
                                                    '[B X] (b x) [C Y]',
                                                    '[C Y] (c y) [D W]'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1 0,2] (1 2)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_7(self):
        """test _1 with a terminator; nothing should be picked up after terminator"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'terminator': ['C']}
        expected = pandas.DataFrame([pandas.Series(['[A] (a) [B]'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1] (1)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_8(self):
        """test _6 with a terminator; nothing should be picked up before terminator"""
        vertical_a = pandas.Series(['A', 'B', 'C', 'D'])
        vertical_b = pandas.Series(['Z', 'X', 'Y', 'W'])
        horizontal_a = pandas.Series(['a', 'b', 'c'])
        horizontal_b = pandas.Series(['z', 'x', 'y'])
        in_val = pandas.DataFrame([vertical_a, vertical_b, horizontal_a, horizontal_b],
                                  index=[['vert', 'vert', 'horiz', 'horiz'],
                                         ['0,1', '0,2', '1', '2']]).T
        setts = {'n': 2, 'terminator': ['X'],
                 'horizontal': [('horiz', '1'), ('horiz', '2')],
                 'vertical': [('vert', '0,1'), ('vert', '0,2')]}
        expected = pandas.DataFrame([pandas.Series(['[C Y] (c y) [D W]'], index=[2])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1 0,2] (1 2)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_9(self):
        """test _8 but longer; things happen before and after terminator"""
        vertical_a = pandas.Series(['A', 'B', 'C', 'D', 'E'])
        vertical_b = pandas.Series(['Z', 'X', 'Y', 'W', 'V'])
        horizontal_b = pandas.Series(['z', 'x', 'y', 'w'])
        horizontal_a = pandas.Series(['a', 'b', 'c', 'd'])
        in_val = pandas.DataFrame([vertical_a, vertical_b, horizontal_a, horizontal_b],
                                  index=[['vert', 'vert', 'horiz', 'horiz'],
                                         ['0,1', '0,2', '1', '2']]).T
        setts = {'n': 2, 'terminator': ['C'],
                 'horizontal': [('horiz', '1'), ('horiz', '2')],
                 'vertical': [('vert', '0,1'), ('vert', '0,2')]}
        expected = pandas.DataFrame([pandas.Series(['[A Z] (a z) [B X]', '[D W] (d w) [E V]'],
                                                   index=[0, 3])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1 0,2] (1 2)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_10(self):
        """test _1 with too few "horizontal" things (should use "continuer" character)"""
        vertical = pandas.concat([pandas.Series(['A', 'B', 'C', 'D'])], axis=1)
        vertical.columns = VERT_DF.columns
        horizontal = pandas.concat([pandas.Series(['a', 'b'])], axis=1)
        horizontal.columns = HORIZ_DF.columns
        setts = {'n': 2, 'horizontal': [('1',)], 'vertical': [('0,1',)],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A a B', 'B b C', 'C _ D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T
        actual = new_ngram.NewNGramIndexer([VERT_DF.iloc[:4, :], HORIZ_DF.iloc[:2, :]], setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_11(self):
        """test _10 with one "horizontal" thing at the end"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal = pandas.Series(['z'], index=[2])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A _ B', 'B _ C', 'C z D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_12(self):
        """test _11 with one missing "horizontal" thing in the middle"""
        vertical = pandas.Series(['A', 'B', 'C', 'D'])
        horizontal = pandas.Series(['a', 'z'], index=[0, 2])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A a B', 'B _ C', 'C z D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_13(self): # XXXX This is an impossible scenario because the horizontal observations must stop one before the vertical ones.
        """test _1 with too few "vertical" things (last should be repeated)"""
        vertical = pandas.Series(['A', 'B', 'C'])
        horizontal = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A a B', 'B b C', 'C c C'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()
        # pdb.set_trace()
        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_14(self):
        """test _13 with one missing "vertical" thing in the middle"""
        vertical = pandas.Series(['A', 'C', 'D'], index=[0, 2, 3])
        horizontal = pandas.Series(['a', 'b', 'c'])
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'use brackets': False}
        expected = pandas.DataFrame([pandas.Series(['A a A', 'A b C', 'C c D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_15(self):
        """longer test, inspired by the first five measures of "Kyrie.krn" parts 1 and 3"""
        vertical = series_maker(VERTICAL_TUPLES)
        horizontal = series_maker(HORIZONTAL_TUPLES)
        in_val = pandas.DataFrame([vertical, horizontal], index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 4, 'horizontal': [('horiz', '1')], 'vertical': [('vert', '0,1')],
                 'continuer': 'P1', 'terminator': 'Rest', 'use brackets': True}
        expected = pandas.DataFrame([series_maker(EXPECTED)],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1] (1)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()
        pdb.set_trace()
        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_16(self):
        """test _9 but with three "vertical" parts and no terminator"""
        vertical_a = pandas.Series(['A', 'B', 'C', 'D', 'E'])
        vertical_b = pandas.Series(['Z', 'X', 'Y', 'W', 'V'])
        vertical_c = pandas.Series(['Q', 'R', 'S', 'T', 'U'])
        horizontal_b = pandas.Series(['z', 'x', 'y', 'w'])
        horizontal_a = pandas.Series(['a', 'b', 'c', 'd'])
        in_val = pandas.DataFrame([vertical_a, vertical_b, vertical_c, horizontal_a, horizontal_b],
                                  index=[['vert', 'vert', 'vert', 'horiz', 'horiz'],
                                         ['0,1', '0,2', '0,3', '2', '3']]).T
        setts = {'n': 2,
                 'horizontal': [('horiz', '2'), ('horiz', '3')],
                 'vertical': [('vert', '0,1'), ('vert', '0,2'), ('vert', '0,3')]}
        expected = pandas.DataFrame([pandas.Series(['[A Z Q] (a z) [B X R]', '[B X R] (b x) [C Y S]',
                                                    '[C Y S] (c y) [D W T]', '[D W T] (d w) [E V U]'],
                                                   index=[0, 1, 2, 3])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1 0,2 0,3] (2 3)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_17(self):
        """test _16 but with four "vertical" parts"""
        vertical_a = pandas.Series(['A', 'B', 'C', 'D', 'E'])
        vertical_b = pandas.Series(['Z', 'X', 'Y', 'W', 'V'])
        vertical_c = pandas.Series(['Q', 'R', 'S', 'T', 'U'])
        vertical_d = pandas.Series(['J', 'K', 'L', 'M', 'N'])
        horizontal_b = pandas.Series(['z', 'x', 'y', 'w'])
        horizontal_a = pandas.Series(['a', 'b', 'c', 'd'])
        in_val = pandas.DataFrame([vertical_a, vertical_b, vertical_c, vertical_d,
                                   horizontal_a, horizontal_b],
                                  index=[['vert', 'vert', 'vert', 'vert', 'horiz', 'horiz'],
                                         ['0,1', '0,2', '0,3', '0,4', '3', '4']]).T
        setts = {'n': 2,
                 'horizontal': [('horiz', '3'), ('horiz', '4')],
                 'vertical': [('vert', '0,1'), ('vert', '0,2'), ('vert', '0,3'), ('vert', '0,4')]}
        expected = pandas.DataFrame([pandas.Series(['[A Z Q J] (a z) [B X R K]',
                                                    '[B X R K] (b x) [C Y S L]',
                                                    '[C Y S L] (c y) [D W T M]',
                                                    '[D W T M] (d w) [E V U N]'],
                                                   index=[0, 1, 2, 3])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1 0,2 0,3 0,4] (3 4)']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_18(self):
        """test _17 but with n=1"""
        vertical_a = pandas.Series(['A', 'B', 'C', 'D', 'E'])
        vertical_b = pandas.Series(['Z', 'X', 'Y', 'W', 'V'])
        vertical_c = pandas.Series(['Q', 'R', 'S', 'T', 'U'])
        vertical_d = pandas.Series(['J', 'K', 'L', 'M', 'N'])
        in_val = pandas.DataFrame([vertical_a, vertical_b, vertical_c, vertical_d],
                                  index=[['vert', 'vert', 'vert', 'vert'],
                                         ['0,1', '0,2', '0,3', '0,4']]).T
        setts = {'n': 1,
                 'vertical': [('vert', '0,1'), ('vert', '0,2'), ('vert', '0,3'), ('vert', '0,4')]}
        expected = pandas.DataFrame([pandas.Series(['[A Z Q J]', '[B X R K]', '[C Y S L]',
                                                    '[D W T M]', '[E V U N]'],
                                                   index=[0, 1, 2, 3, 4])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0,1 0,2 0,3 0,4]']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_19(self):
        # test _0 with a "missing" vertical and horizontal thing
        # Input:
        #    0  1  2  3  4
        # v: A  B  C     D
        # h:    a     b  c
        #
        # Expected:
        # 0: 'A a B'
        # 1: 'B _ C'
        # 2: 'C b C'
        # 3: 'C c D'
        # NB: this started as a regression test for issue 261, where missing values weren't filled
        vertical = pandas.Series(['A', 'B', 'C', 'D'], index=[0, 1, 2, 4])
        horizontal = pandas.Series(['a', 'b', 'c'], index=[0, 2, 3])
        in_val = pandas.DataFrame([vertical, horizontal],
                                  index=[['vert', 'horiz'], ['0,1', '1']]).T
        setts = {'n': 2, 'mark singles': False, 'horizontal': [('horiz', '1')],
                 'vertical': [('vert', '0,1')]}
        expected = pandas.DataFrame([pandas.Series(['A a B', 'B _ C', 'C b C', 'C c D'])],
                                    index=[['new_ngram.NewNGramIndexer'], ['0,1 1']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))

    def test_ngram_20(self):
        """
        Ensure that events in other voices don't erroneously cause events in the voices-under-study.

        Regression test for GH#334.
        """
        # NB: it looks like this:
        #
        #    0 | .5 | 1 | .5 | 2 | .5 | 3  <-- offset/index
        # A: A |    | B |    | C |    | D  <-- included voice
        # B: Q | W  |   |    | E | R  |    <-- included voice
        # C:   | Z  |   | X  | V | N  |    <-- not included
        #
        # NOTE: for this to be a sufficient test, there must be an offset like 0.5, where one part
        #       has an event but the other has NaN, *and* an offset like 1.5, where both included
        #       parts do not have events, but the not-included part does.
        vertical_a = pandas.Series(['A', 'B', 'C', 'D'], index=[0.0, 1.0, 2.0, 3.0])
        vertical_b = pandas.Series(['Q', 'W', 'E', 'R'], index=[0.0, 0.5, 2.0, 2.5])
        vertical_c = pandas.Series(['Z', 'X', 'V', 'N'], index=[0.5, 1.5, 2.0, 2.5])
        in_val = pandas.DataFrame([vertical_a, vertical_b, vertical_c],
                                  index=[['vert', 'vert', 'vert'], ['0', '1', '2']]).T
        setts = {'n': 2, 'vertical': [('vert', '0'), ('vert', '1')]}
        expected = ['[A Q] [A W]', '[A W] [B W]', '[B W] [C E]', '[C E] [C R]', '[C R] [D R]']
        expected = pandas.DataFrame([pandas.Series(expected, index=[0.0, 0.5, 1.0, 2.0, 2.5])],
                                    index=[['new_ngram.NewNGramIndexer'], ['[0 1]']]).T

        actual = new_ngram.NewNGramIndexer(in_val, setts).run()

        self.assertSequenceEqual(list(expected.columns), list(actual.columns))
        self.assertEqual(len(expected), len(actual))
        for col_name in expected.columns:
            self.assertSequenceEqual(list(expected[col_name].index), list(actual[col_name].index))
            self.assertSequenceEqual(list(expected[col_name].values), list(actual[col_name].values))


#--------------------------------------------------------------------------------------------------#
# Definitions                                                                                      #
#--------------------------------------------------------------------------------------------------#
NEW_NGRAM_INDEXER_SUITE = unittest.TestLoader().loadTestsFromTestCase(TestNewNGramIndexer)
