#! /usr/bin/python
# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------
# Program Name:              vis
# Program Description:       Measures sequences of vertical intervals.
#
# Filename: Experimenter.py
# Purpose: Holds the Experimenter controller.
#
# Copyright (C) 2012, 2013 Jamie Klassen, Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
"""
Holds the Experimenter controller.
"""

# Imports from...
# python
from copy import deepcopy
# PyQt4
from PyQt4 import QtCore
# music21
from music21 import chord, converter, stream, note, interval, roman
# vis
from controller import Controller
from models import analyzing
from models.experimenting import ExperimentSettings
from models import ngram
import OutputLilyPond


class Experimenter(Controller, QtCore.QObject):
    """
    This class handles input for a user's choice of Experiment and choice
    of associated Settings, then performs the experiment, returning the
    relevant Results object(s).
    """

    # PyQt4 Signals
    # -------------
    # a 2-tuple: a string for a setting name and the value for the setting
    set = QtCore.pyqtSignal(tuple)
    # tell the Experimenter controller to perform an experiment
    run_experiment = QtCore.pyqtSignal()
    # Emitted by the Experimenter when the experiment is finished. The argument is a tuple, where
    # the first element is the type of Display object to use, and the second is the data required
    # by the Display object.
    experiment_finished = QtCore.pyqtSignal(tuple)
    # description of an error in the Experimenter
    error = QtCore.pyqtSignal(str)
    # informs the GUI of the status for a currently-running experiment (if two
    # or three characters followed by a '%' then it should try to update a
    # progress bar, if available)
    status = QtCore.pyqtSignal(str)
    # Emitted by an Experiment when it's finished. The argument should be a QVariant that holds
    # whatever type is required by the relevant Display class.
    _experiment_results = QtCore.pyqtSignal(QtCore.QVariant)

    # List of the experiments we have
    # TODO: do this with introspection so we don't have to update things
    # in multiple places when these change.
    experiments_we_have = ['IntervalsList', 'ChordsList']

    def __init__(self):
        """
        Create a new Experimenter controller.
        """
        super(Experimenter, self).__init__()  # required for signals
        self._list_of_analyses = None
        self._experiment_settings = ExperimentSettings()
        # Signals
        self.set.connect(self._change_setting)
        self.run_experiment.connect(self._run_experiment)
        self._experiment_results.connect(self._catch_experiments)
        # Hold the result emitted by an Experiment when it's finished
        self._exper_result = None

    @QtCore.pyqtSlot(list)
    def catch_analyses(self, analyses_list):
        """
        Slot for the Analyzer.analysis_finished signal. This method is called
        when the Analyzer controller has finished analysis.

        The argument is a list of AnalysisRecord objects.
        """
        self._list_of_analyses = analyses_list

    @QtCore.pyqtSlot(QtCore.QVariant)
    def _catch_experiments(self, experiment_result):
        """
        Slot for the Experimenter._experiment_results signal. Catches the result, converts it to a
        python object, then assigns it to the Experimenter._exper_result instance variable.

        The argument is a QVariant object.
        """
        # Update the status
        self.status.emit('100')
        self.status.emit('Waiting on DisplayHandler')

        # Make and emit the tuple for the DisplayHandler
        self.experiment_finished.emit((self._exper_result, experiment_result.toPyObject()))

        # Clear the settings used for this experiment, so they don't accidentally carry over to the
        # next experiment.
        self._experiment_settings = ExperimentSettings()

    @QtCore.pyqtSlot()  # for Experimenter.run_experiment
    def _run_experiment(self):
        """
        Runs the currently-configured experiment(s).
        """
        # Check there is an 'experiment' setting that refers to one we have

        if self._experiment_settings.get('experiment') == 'IntervalsLists':
            exper = IntervalsLists
        elif self._experiment_settings.get('experiment') == 'ChordsList':
            exper = ChordsLists
        elif self._experiment_settings.get('experiment') == 'IntervalsStatistics':
            exper = IntervalsStatistics
        elif self._experiment_settings.get('experiment') == 'IntervalNGramStatistics':
            exper = IntervalNGramStatistics
        elif self._experiment_settings.get('experiment') == 'LilyPondExperiment':
            exper = LilyPondExperiment
        else:
            self.error.emit('Experimenter: could not determine which experiment to run.')
            return

        # Trigger the experiment
        try:
            exper = exper(self, self._list_of_analyses, self._experiment_settings)
        except KeyError as kerr:
            # If the experiment doesn't have the ExperimentSettings it needs
            self.error.emit(kerr.message)
            return

        # Get the preferred (or possible) Display subclasses for this Experiment
        self._exper_result = exper.good_for()

        # add to the QThreadPool
        QtCore.QThreadPool.globalInstance().start(exper)
        self.status.emit('0')
        self.status.emit('Experiment running... the progress bar will not be updated.')

    @QtCore.pyqtSlot(tuple)  # for Experimenter.set
    def _change_setting(self, sett):
        """
        Given a 2-tuple, where the first element is a string (setting name) and
        the second element is any type (setting value), make that setting refer
        to that value.
        """
        self._experiment_settings.set(sett[0], sett[1])


class Experiment(QtCore.QRunnable):
    # NOTE: in subclasses, change "QtCore.QRunnable" to "Experiment"
    """
    Base class for all Experiments.
    """

    # List of strings that are the names of the Display objects suitable for this Experiment
    _good_for = ['None']

    def __init__(self, controller, records, settings):
        """
        Create a new Experiment.

        There are three mandatory arguments:
        - controller : the Experimenter object to which this Experiment belongs
        - records : a list of AnalysisRecord objects
        - settings : an ExperimentSettings object
        """
        # NOTE: In subclasses, you should implement a check system to ensure the
        #       ExperimentSettings object has the right settings in it. If you do
        #       not have the settings you need, send an error through the
        #       Experimenter controller, then return without proper instantiation:
        # self._controller.error.emit(error_message_here)
        # return
        # NOTE: In subclasses, the following line should be like this:
        #       super(SubclassName, self).__init__(records, settings)
        super(Experiment, self).__init__()
        self._controller = controller
        self._records = records
        self._settings = settings

    def good_for(self):
        """
        Returns a list of string objects that are the names of the Display objects suitable for
        this Experiment
        """
        # NOTE: You do not need to reimplement this method in subclasses.
        return self._good_for

    def run(self):
        """
        Collect the results of perform(), then emit the signal that sends them to the Experimenter
        """
        # Note 1: Do not need to reimplement this method in subclasses.
        signal_me = None
        try:
            signal_me = self.perform()
        except Exception as exc:
            self._controller.error.emit(u'Failure during experiment.\n\n' + str(type(exc)) +
                u' says:\n' + str(exc))
            self._controller.experiment_finished.emit((u'error', None))
        else:
            self._controller._experiment_results.emit(QtCore.QVariant(signal_me))

    def perform(self):
        """
        Perform the Experiment. This method is not called "run" to avoid possible
        confusion with the multiprocessing nature of Experiment subclasses.

        This method emits an Experimenter.experimented signal when it finishes.
        """
        # NOTE: You must reimplement this method in subclasses.
        pass


class IntervalsLists(Experiment):
    """
    Prepare a list of 3-tuples:
    [(vertical_interval, horizontal_interval, offset),
    (vertical_interval, horizontal_interval, offset)]

    BUT: the first element in the ouputted list is a tuple of strings that represent descriptions
    of the data in each tuple index that are suitable for use in a spreadsheet.

    Each horizontal interval specifies the movement of the lower part in going to the following
    chord.

    This Experiment can be outputted by these Display classes:
    - SpreadsheetFile
    - LilyPondAnnotated

    Although the Experiment itself does not use NGram objects or deal with
    n-grams (only intervals), both output formats are useful for visual
    inspections that allow human to find n-grams.
    """

    # List of strings that are the names of the Display objects suitable for this Experiment
    _good_for = ['SpreadsheetFile', 'LilyPondAnnotated']

    def __init__(self, controller, records, settings):
        """
        Create a new IntervalsLists Experiment.

        Parameters
        ----------

        controller : Experimenter
            The Experimenter instance that runs this IntervalsLists.

        records : list of AnalysisRecord
            The objects to use for analysis.

        settings : ExperimentSettings
            The settings to use for this IntervalsLists. The required settings are...
            - 'quality' : boolean, whether to print or suppress quality
            - 'simple or compound' : whether to print intervals in their single-octave
                ('simple') or actual ('compound') form.
            - 'output format' : choose the Display subclass for this Experiment's results.

        Raises
        ------

        KeyError:
            If one of the required settings is not present in the ExperimentSettings instance.
        """
        # Call the superclass constructor
        super(IntervalsLists, self).__init__(controller, records, settings)

        # Check the ExperimentSettings object has the right settings
        if not settings.has('quality') or not settings.has('simple or compound'):
            msg = 'IntervalsLists requires "quality" and "simple or compound" settings'
            raise KeyError(msg)

        # Process the optional "output format" setting
        if self._settings.has('output format'):
            self._good_for = [self._settings.get('output format')]

    @staticmethod
    def interval_formatter(interv, quality, size, direction):
        # TODO: this should be tested
        """
        Format the output of an Interval object according to certain preferences.

        Parameters
        ----------

        interv : music21.interval.Interval
            This object will be formatted.

        quality : boolean
            Whether to include a symbol for the interval's quality.

        size : string
            Either 'simple' or 'compound', depending on whether the interval should be reduced to
            its single-octave size, if relevant.

        direction : boolean or string
            Whether to print a + or - sign indicating the interval's direction. The string
            'sometimes' will print the direction only if it is negative.

        Returns
        -------

        string
            A representation of the inputted Interval instance.
        """
        post = u''

        if direction is True:
            if interv.direction > 0:
                post = u'+'
            elif interv.direction < 0:
                post = u'-'
        elif u'sometimes' == direction and -1 == interv.direction:
            post = u'-'

        if quality:
            # We must get all of the quality, and none of the size (important for AA, dd, etc.)
            qual = u''
            for each in interv.name:
                if each in [u'A', u'M', u'P', u'm', u'd']:
                    qual += each
            post += qual

        if 'simple' == size:
            post += u'8' if 8 == interv.generic.undirected else \
                unicode(interv.generic.simpleUndirected)
        else:
            post += unicode(interv.generic.undirected)

        return post

    def perform(self):
        """
        Perform the IntervalsLists Experiment.
        """

        # pre-fetch the settings we'll be using repeatedly
        quality = self._settings.get('quality')
        interval_size = self._settings.get('simple or compound')
        include_direction = not self._settings.get('ignore direction')
        include_direction = False if not include_direction else u'sometimes'

        # this is the header for CSV-format output
        data = [(u'vertical', u'horizontal', u'offset')]

        # loop through every AnalysisRecord
        for record in self._records:
            # loop through all the events... this use of zip() works like this:
            #    a_list = (1, 2, 3, 4)
            #    zip(a_list, list(a_list)[1:])
            #    ((1, 2), (2, 3), (3, 4))
            for first, second in zip(record, list(record)[1:]):
                offset = first[0]
                # lower note of the fist interval
                first_lower = first[1][0]
                # upper note of the first interval
                first_upper = first[1][1]
                # lower note of the second interval
                second_lower = second[1][0]

                # these will hold the intervals
                vertical, horizontal = None, None

                # If one of the notes is actually a 'Rest' then we can't use it, so skip it
                if 'Rest' == first_lower:
                    vertical = u'Rest & ' + first_upper
                    horizontal = u'N/A'
                elif 'Rest' == first_upper:
                    vertical = first_lower + u' & Rest'
                else:
                    # make the vertical interval, which connects first_lower and first_upper
                    vertical = IntervalsLists.interval_formatter(
                        interval.Interval(note.Note(first_lower), note.Note(first_upper)),
                        quality=quality,
                        size=interval_size,
                        direction=include_direction)

                if 'Rest' == second_lower:
                    horizontal = u'N/A'
                elif horizontal is None:
                    # make the horizontal interval, which connects first_lower and second_lower
                    horizontal = IntervalsLists.interval_formatter(
                        interval.Interval(note.Note(first_lower), note.Note(second_lower)),
                        quality=quality,
                        size=interval_size,
                        direction=True)

                # make the 3-tuple to append to the list
                put_me = (vertical, horizontal, offset)

                data.append(put_me)

            # finally, add the last row, which has no horizontal connection
            last = record[-1]
            last_upper = None
            last_lower = None
            last_vertical = None
            if 'Rest' == last[1][0]:
                last_upper = u'Rest'
            if 'Rest' == last[1][1]:
                last_lower = u'Rest'
            if last_upper is not None or last_lower is not None:
                last_vertical = u'N/A'
            else:
                last_vertical = IntervalsLists.interval_formatter(
                    interval.Interval(note.Note(last[1][0]), note.Note(last[1][1])),
                    quality=quality,
                    size=interval_size,
                    direction=include_direction)
            data.append((last_vertical, None, last[0]))

        return data


class ChordsLists(Experiment):
    """
    Prepare a list of 3-tuples:
    [(chord_name, neoriemannian_transformation, offset),
    (chord_name, neoriemannian_transformation, offset)]

    BUT: the first element in the ouputted list is a tuple of strings that represent descriptions
    of the data in each tuple index that are suitable for use in a spreadsheet.

    Each transformation specifies how to get to the following chord.

    This Experiment can be outputted by these Display classes:
    - SpreadsheetFile
    - LilyPondAnnotated

    The experiment uses ChordNGram objects to find the transformation.
    """

    # List of strings that are the names of the Display objects suitable for this Experiment
    _good_for = ['SpreadsheetFile', 'LilyPondAnnotated']

    # How chord qualities should be represented with single letters
    _quality_dict = {u'major': u'+', u'minor': u'-', u'augmented': u'x', u'diminished': u'o'}

    def __init__(self, controller, records, settings):
        """
        Create a new ChordsLists.

        There are three mandatory arguments:
        - controller : the Experimenter object to which this Experiment belongs
        - records : a list of AnalysisRecord objects
        - settings : an ExperimentSettings object

        ChordsLists can use this setting, but will not provide a default:
        - output format : choose the Display subclass for this experiment's results
        """
        # Call the superclass constructor
        super(ChordsLists, self).__init__(controller, records, settings)

        # Process the optional "output format" setting
        if self._settings.has('output format'):
            self._good_for = [self._settings.get('output format')]

    @staticmethod
    def make_chord_symbol(the_chord):
        """
        Given a music21.chord.Chord, make a chord symbol.

        Parameters
        ----------

        the_chord : music21.chord.Chord
            The chord the symbol of which you want.

        Returns
        -------

        string
            The corresponding chord symbol.
        """
        the_figure = roman.romanNumeralFromChord(the_chord).figure[1:]
        if u'other' == the_chord.quality:
            # We'll show bass and FB
            bass_name = unicode(the_chord.bass().name).replace(u'-', u'b')  # replace flat symbols
            return u''.join([bass_name, u' ', the_figure]) if the_figure != u'' else bass_name
        else:
            # We'll show root, quality, and FB
            root = unicode(the_chord.root().name).replace(u'-', u'b')  # replace flat symbols
            u''.join([root, ChordsLists._quality_dict[the_chord.quality]])
            return u''.join([root, u' ', the_figure]) if the_figure != u'' else root

    @staticmethod
    def remove_rests(event):
        """
        Remove 'Rest' strings from iterables of strings.

        Parameters
        ----------

        event : list or tuple of strings, optionally with singly-nested lists/tuples of strings
            'Rest' strings will be removed from this

        Returns
        -------

        tuple of strings
            All elements are brought into the main tuple, and any strings == u'Rest' are removed
        """
        post = []
        for chord_member in event:
            if isinstance(chord_member, tuple) or isinstance(chord_member, list):
                for inner_chord_member in chord_member:
                    if u'Rest' != inner_chord_member:
                        post.append(inner_chord_member)
            elif u'Rest' != chord_member:
                post.append(chord_member)
        return post

    def perform(self):
        """
        Perform the ChordsListsExperiment.

        This method emits an Experimenter.experimented signal when it finishes.
        """

        # Should we use the ChordParser?
        if self._settings.has('chord parse length'):
            cp = ChordParser(self._controller, self._records, self._settings)
            res = cp.perform()
            self._records = res if res is not None else self._records
            if res is None:
                return None

        # this is what we'll return
        post = [('chord', 'transformation', 'offset')]

        # keep a dict of Note objects to help speed up Chord.__init__()
        note_dict = {}

        for record in self._records:
            for first, second in zip(record, list(record)[1:]):
                # prepare the string-wise representation of notes in the chords
                first_chord_str = ChordsLists.remove_rests(first[1])
                second_chord_str = ChordsLists.remove_rests(second[1])
                first_chord_pitches = []
                for each in first_chord_str:
                    try:
                        first_chord_pitches.append(note_dict[each])
                    except KeyError:
                        note_dict[each] = note.Note(each)
                        first_chord_pitches.append(note_dict[each])
                second_chord_pitches = []
                for each in second_chord_str:
                    try:
                        second_chord_pitches.append(note_dict[each])
                    except KeyError:
                        note_dict[each] = note.Note(each)
                        second_chord_pitches.append(note_dict[each])
                first_chord = chord.Chord(first_chord_pitches)
                second_chord = chord.Chord(second_chord_pitches)

                # ensure neither of the chords is just a REST... if it is, we'll skip this loop
                if u'' == first_chord or u'' == second_chord:
                    continue

                # make the chord symbol
                chord_name = ChordsLists.make_chord_symbol(chord.Chord(first_chord))

                # find the transformation
                horizontal = ngram.ChordNGram.find_transformation(chord.Chord(first_chord),
                                                                  chord.Chord(second_chord))
                put_me = (chord_name, u'(' + horizontal + u')', first[0])

                # add this chord-and-transformation to the list of all of them
                post.append(put_me)

            # finally, add the last chord, which doesn't have a transformation
            last_chord = ChordsLists.remove_rests(record[-1][1])

            # format and add the chord, but only if the previous step didn't turn everyting to rests
            if '' != last_chord:
                post.append((ChordsLists.make_chord_symbol(chord.Chord(last_chord)),
                             None,
                             record[-1][0]))

        return post


class IntervalsStatistics(Experiment):
    """
    Experiment that gathers statistics about the number of occurrences of vertical intervals.

    Produce a list of tuples, like this:
    [('m3', 10), ('M3', 4), ...]

    The list is sorted as per the ExperimentSettings. Each 0th element in the tuple is a
    string-format representation of an interval, and each 1st element is the number of occurrences.

    Intervals that do not occur in any of the AnalysisRecord objects are not included in the output.
    """

    # List of strings that are the names of the Display objects suitable for this Experiment
    _good_for = ['StatisticsListDisplay', 'StatisticsChartDisplay']

    def __init__(self, controller, records, settings):
        """
        Create a new IntervalsStatistics experiment.

        There are three mandatory arguments:
        - controller : the Experimenter object to which this Experiment belongs
        - records : a list of AnalysisRecord objects
        - settings : an ExperimentSettings object

        IntervalsStatistics requires these settings:
        - quality : whether or not to display interval quality
        - simple or compound : whether to use simple or compound intervals

        IntervalsStatistics uses these settings, but provides defaults:
        - topX : display on the "top X" number of results (default: none)
        - threshold : stop displaying things after this point (default: none)
        - sort order : whether to sort things 'ascending' or 'descending' (default: 'descending')
        - sort by : whether to sort things by 'frequency' or 'name' (default: 'frequency')

        IntervalsStatistics can use this setting, but will not provide a default:
        - output format : choose the Display subclass for this experiment's results
        """
        super(IntervalsStatistics, self).__init__(controller, records, settings)

        # Check the ExperimentSettings object has the right settings
        if not settings.has('quality') or not settings.has('simple or compound'):
            msg = 'IntervalsStatistics requires "quality" and "simple or compound" settings'
            raise KeyError(msg)

        # Check for the other settings we use, and provide default values if required
        if not self._settings.has('topX'):
            self._settings.set('topX', None)
        if not self._settings.has('threshold'):
            self._settings.set('threshold', None)
        if not self._settings.has('sort order'):
            self._settings.set('sort order', 'descending')
        if not self._settings.has('sort by'):
            self._settings.set('sort by', 'frequency')

        # Make a dictionary to store the intervals
        self._intervals = None

        # Make a list to store the sorted and filtered intervals
        self._keys = None

        # Process the optional "output format" setting
        if self._settings.has('output format'):
            self._good_for = [self._settings.get('output format')]

    def _add_interval(self, interv):
        """
        Add an interval, represented as a string, to the occurrences dictionary in this experiment.
        """
        if interv in self._intervals:
            self._intervals[interv] += 1
        else:
            self._intervals[interv] = 1

    @staticmethod
    def interval_sorter(left, right):
        """
        Returns -1 if the first argument is a smaller interval.
        Returns 1 if the second argument is a smaller interval.
        Returns 0 if both arguments are the same.

        Input should be a str of the following form:
        - d, m, M, or A
        - an int

        Examples:
        >>> from vis import interval_sorter
        >>> interval_sorter( 'm3', 'm3' )
        0
        >>> interval_sorter( 'm3', 'M3' )
        1
        >>> interval_sorter( 'A4', 'd4' )
        -1
        """

        string_digits = '0123456789'
        list_of_directions = ['+', '-']

        # I want to sort based on generic size, so the direction is irrelevant. If
        # we have directions, they'll be removed with this. If we don't have
        # directions, this will have no effect.
        for direct in list_of_directions:
            left = left.replace(direct, '')
            right = right.replace(direct, '')

        # If we have numbers with no qualities, we'll just add a 'P' to both, to
        # pretend they have the same quality (which, as far as we know, they do).
        if left[0] in string_digits and right[0] in string_digits:
            left = 'P' + left
            right = 'P' + right

        # Comparisons!
        if left == right:
            post = 0
        elif int(left[1:]) < int(right[1:]):  # if x is generically smaller
            post = -1
        elif int(left[1:]) > int(right[1:]):  # if y is generically smaller
            post = 1
        else:  # otherwise, we're down to the species/quality
            left_qual = left[0]
            right_qual = right[0]
            if left_qual == 'd':
                post = -1
            elif right_qual == 'd':
                post = 1
            elif left_qual == 'A':
                post = 1
            elif right_qual == 'A':
                post = -1
            elif left_qual == 'm':
                post = -1
            elif right_qual == 'm':
                post = 1
            else:
                post = 0

        return post

    def perform(self):
        """
        Perform the Experiment. This method is not called "run" to avoid possible
        confusion with the multiprocessing nature of Experiment subclasses.

        This method emits an Experimenter.experimented signal when it finishes.
        """
        # (0) Instantiate/clear things
        self._intervals = {}
        self._keys = []

        # (1) Loop through each of the AnalysisRecord objects, adding the intervals we find.
        # We'll use these over and over again
        quality = self._settings.get('quality')
        interval_size = self._settings.get('simple or compound')
        include_direction = not self._settings.get('ignore direction')

        for each_record in self._records:
            for each_event in each_record:
                # make sure we don't try to make an Interval from a rest or a chord
                if isinstance(each_event[1][0], basestring) and \
                isinstance(each_event[1][1], basestring):
                    this_interval = None
                    if 'Rest' != each_event[1][0] and 'Rest' != each_event[1][1]:
                        this_interval = interval.Interval(note.Note(each_event[1][0]),
                                                          note.Note(each_event[1][1]))
                    else:
                        continue
                    self._add_interval(IntervalsLists.interval_formatter(this_interval,
                        quality=quality,
                        size=interval_size,
                        direction=include_direction))

        # (2.1) If there is a topX or threshold filter, sort by frequency now.
        if self._settings.get('topX') is not None or \
        self._settings.get('threshold') is not None:
            # returns a list of keys, sorted by descending frequency
            self._keys = sorted(self._intervals, key=lambda x: self._intervals[x], reverse=True)

            # (3) If we're doing a "topX" filter, do it now.
            if self._settings.get('topX') is not None:
                # cut the list at the "topX-th element"
                self._keys = self._keys[:int(self._settings.get('topX'))]

            # (4) If we're doing a "threshold" filter, do it now.
            if self._settings.get('threshold') is not None:
                thresh = int(self._settings.get('threshold'))
                # if the last key on the list is already greater than the threshold, we won't sort
                if self._intervals[self._keys[-1]] < thresh:
                    # hold the keys of intervals above the threshold
                    new_keys = []
                    # check each key we already have, and add it to new_keys only if its
                    # occurrences are above the threshold value
                    for each_key in self._keys:
                        if self._intervals[each_key] >= thresh:
                            new_keys.append(each_key)
                    # assign
                    self._keys = new_keys
        # (2.2) Otherwise, just get all the keys
        else:
            self._keys = self._intervals.keys()

        # (4) Now do a final sorting.
        # Should we 'reverse' the list sorting? Yes, unless we sorted 'ascending'
        should_reverse = False if 'ascending' == self._settings.get('sort order') else True

        if 'frequency' == self._settings.get('sort by'):
            self._keys = sorted(self._keys,
                                key=lambda x: self._intervals[x],
                                reverse=should_reverse)
        else:
            self._keys = sorted(self._keys,
                                cmp=IntervalsStatistics.interval_sorter,
                                reverse=should_reverse)

        # (5) Construct the dictionary to return
        post = []
        for each_key in self._keys:
            post.append((each_key, self._intervals[each_key]))

        # (6) Conclude
        return post


class IntervalNGramStatistics(Experiment):
    """
    Experiment that gathers statistics about the number of occurrences of n-grams composed of
    vertical intervals and the horizontal connections between the lower voice.

    Produce a list of tuples, like this:
    [('m3 -P4 M6', 10), ('M3 -P4 m6', 4), ...]

    The list is sorted as per the ExperimentSettings. Each 0th element in the tuple is a
    string-format representation of an interval, and each 1st element is the number of occurrences.

    Intervals that do not occur in any of the AnalysisRecord objects are not included in the output.
    """

    # List of strings that are the names of the Display objects suitable for this Experiment
    _good_for = ['StatisticsListDisplay', 'StatisticsChartDisplay']

    def __init__(self, controller, records, settings):
        """
        Create a new IntervalNGramStatistics experiment.

        There are three mandatory arguments:
        - controller : the Experimenter object to which this Experiment belongs
        - records : a list of AnalysisRecord objects
        - settings : an ExperimentSettings object

        IntervalNGramStatistics requires these settings:
        - quality : whether or not to display interval quality
        - simple or compound : whether to use simple or compound intervals
        - values of n : a list of ints that is the values of 'n' to display

        IntervalNGramStatistics uses these settings, but provides defaults:
        - topX : display on the "top X" number of results (default: none)
        - threshold : stop displaying things after this point (default: none)
        - sort order : whether to sort things 'ascending' or 'descending' (default: 'descending')
        - sort by : whether to sort things by 'frequency' or 'name' (default: 'frequency')

        IntervalNGramStatistics can use this setting, but will not provide a default:
        - output format : choose the Display subclass for this experiment's results
        """
        super(IntervalNGramStatistics, self).__init__(controller, records, settings)

        # Check the ExperimentSettings object has the right settings
        if not settings.has('quality') or not settings.has('simple or compound') or \
        not settings.has('values of n'):
            msg = 'IntervalNGramStatistics requires "quality," '
            msg += '"simple or compound," and "values of n" settings'
            raise KeyError(msg)

        # Check for the other settings we use, and provide default values if required
        if not self._settings.has('topX'):
            self._settings.set('topX', None)
        if not self._settings.has('threshold'):
            self._settings.set('threshold', None)
        if not self._settings.has('sort order'):
            self._settings.set('sort order', 'descending')
        if not self._settings.has('sort by'):
            self._settings.set('sort by', 'frequency')

        # Make a dictionary to store the intervals
        self._ngrams = None

        # Make a list to store the sorted and filtered intervals
        self._keys = None

        # Process the optional "output format" setting
        if self._settings.has('output format'):
            self._good_for = [self._settings.get('output format')]

    def _add_ngram(self, interv):
        """
        Add an n-gram, represented as a string, to the occurrences dictionary in this experiment.
        """
        if interv in self._ngrams:
            self._ngrams[interv] += 1
        else:
            self._ngrams[interv] = 1

    # TODO: implement vis7 tests for this
    @staticmethod
    def ngram_sorter(left, right):
        """
        Returns -1 if the first argument is a smaller n-gram.
        Returns 1 if the second argument is a smaller n-gram.
        Returns 0 if both arguments are the same.

        If one n-gram is a subset of the other, starting at index 0, we consider the
        shorter n-gram to be the "smaller."

        Input should be like this, at minimum with three non-white-space characters
        separated by at most one space character.
        3 +4 7
        m3 +P4 m7
        -3 +4 1
        m-3 +P4 P1

        Examples:
        >>> from vis import ngram_sorter
        >>> ngram_sorter( '3 +4 7', '5 +2 4' )
        -1
        >>> ngram_sorter( '3 +5 6', '3 +4 6' )
        1
        >>> ngram_sorter( 'M3 1 m2', 'M3 1 M2' )
        -1
        >>> ngram_sorter( '9 -2 -3', '9 -2 -3' )
        0
        >>> ngram_sorter( '3 -2 3 -2 3', '6 +2 6' )
        -1
        >>> ngram_sorter( '3 -2 3 -2 3', '3 -2 3' )
        1
        """

        # We need the string version for this
        left = str(left)
        right = str(right)

        # Just in case there are some extra spaces
        left = left.strip()
        right = right.strip()

        # See if we have only one interval left. When there is only one interval,
        # the result of this will be -1
        left_find = left.find(' ')
        right_find = right.find(' ')

        if -1 == left_find:
            if -1 == right_find:
                # Both x and y have only one interval left, so the best we can do is
                # the output from intervalSorter()
                return IntervalsStatistics.interval_sorter(left, right)
            else:
                # x has one interval left, but y has more than one, so x is shorter.
                return -1
        elif -1 == right_find:
            # y has one interval left, but x has more than one, so y is shorter.
            return 1

        # See if the first interval will differentiate
        possible_result = IntervalsStatistics.interval_sorter(left[:left_find], right[:right_find])

        if 0 != possible_result:
            return possible_result

        # If not, we'll rely on ourselves to solve the next mystery!
        return IntervalNGramStatistics.ngram_sorter(left[left_find + 1:], right[right_find + 1:])

    def perform(self):
        """
        Perform the Experiment. This method is not called "run" to avoid possible
        confusion with the multiprocessing nature of Experiment subclasses.

        This method emits an Experimenter.experimented signal when it finishes.
        """
        # (0) Instantiate/clear things
        self._ngrams = {}
        self._keys = []

        # (1) Loop through each of the AnalysisRecord objects, adding the n-grams we find.
        # We'll use these over and over again
        quality = self._settings.get('quality')
        interval_size = self._settings.get('simple or compound')
        values_of_n = sorted(self._settings.get('values of n'))  # sorted lowest-to-highest
        use_canonical = self._settings.get('ignore direction')

        for each_record in self._records:
            for i in xrange(len(each_record)):
                # store the last index in this record, so we know if we're about to cause
                # an IndexError
                last_index = len(each_record) - 1

                # make sure our first vertical interval doesn't have a rest
                if 'Rest' == each_record[i][1][0] or 'Rest' == each_record[i][1][1]:
                    continue

                # for the next loop, we'll use this to indicate that the current and all higher
                # values of 'n' do not have enough vertical intervals without rests
                kill_switch = False

                # for each of the values of 'n' we have to find:
                for each_n in values_of_n:
                    # start of the intervals to build the n-gram with this 'n' value
                    intervals_this_n = [interval.Interval(note.Note(each_record[i][1][0]),
                                                          note.Note(each_record[i][1][1]))]

                    # reset the kill_switch
                    kill_switch = False

                    # - first check if there are enough vertical intervals without rests
                    #   (if not, we'll skip this and all higher 'n' values with "kill_switch")
                    for j in xrange(1, each_n):
                        # this first check will ensure we don't cause an IndexError going past
                        # the end of the list
                        if i + j > last_index:
                            kill_switch = True
                            break
                        # now check for rests
                        elif 'Rest' == each_record[i + j][1][0] or \
                        'Rest' == each_record[i + j][1][1]:
                            kill_switch = True
                            break
                        # now assume we can make an n-gram
                        else:
                            this_interv = interval.Interval(note.Note(each_record[i + j][1][0]),
                                                            note.Note(each_record[i + j][1][1]))
                            intervals_this_n.append(this_interv)
                    if kill_switch:
                        break

                    # - build the n-gram
                    this_ngram = ngram.IntervalNGram(intervals_this_n)

                    # - find the n-gram's string-wise representation
                    # - add the representation to the occurrences dictionary
                    add_me = None
                    if use_canonical:
                        add_me = this_ngram.canonical(quality, interval_size)
                    else:
                        add_me = this_ngram.get_string_version(quality, interval_size)
                    self._add_ngram(add_me)
        # (End of step 1)

        # (2.1) If there is a topX or threshold filter, sort by frequency now.
        if self._settings.get('topX') is not None or \
        self._settings.get('threshold') is not None:
            # returns a list of keys, sorted by descending frequency
            self._keys = sorted(self._ngrams, key=lambda x: self._ngrams[x], reverse=True)

            # (3) If we're doing a "topX" filter, do it now.
            if self._settings.get('topX') is not None:
                # cut the list at the "topX-th element"
                self._keys = self._keys[:int(self._settings.get('topX'))]

            # (4) If we're doing a "threshold" filter, do it now.
            if self._settings.get('threshold') is not None:
                thresh = int(self._settings.get('threshold'))
                # if the last key on the list is already greater than the threshold, we won't sort
                if self._ngrams[self._keys[-1]] < thresh:
                    # hold the keys of intervals above the threshold
                    new_keys = []
                    # check each key we already have, and add it to new_keys only if its
                    # occurrences are above the threshold value
                    for each_key in self._keys:
                        if self._ngrams[each_key] >= thresh:
                            new_keys.append(each_key)
                    # assign
                    self._keys = new_keys
        # (2.2) Otherwise, just get all the keys
        else:
            self._keys = self._ngrams.keys()

        # (4) Now do a final sorting.
        # Should we 'reverse' the list sorting? Yes, unless we sorted 'ascending'
        should_reverse = False if 'ascending' == self._settings.get('sort order') else True

        if 'frequency' == self._settings.get('sort by'):
            self._keys = sorted(self._keys,
                                key=lambda x: self._ngrams[x],
                                reverse=should_reverse)
        else:
            self._keys = sorted(self._keys,
                                cmp=IntervalsStatistics.interval_sorter,
                                reverse=should_reverse)

        # (5) Construct the dictionary to return
        # (5a) Make a crafty tag to help with the description
        desc = u'Interval ' + unicode(values_of_n[0]) + u'-Grams\n'
        desc += u'Sorted ' + self._settings.get('sort order') + u' by ' + \
            self._settings.get('sort by') + u'\n'
        if self._settings.get('topX'):
            desc += u'Including only the top ' + unicode(self._settings.get('topX')) + u'\n'
        if self._settings.get('threshold'):
            desc += u'With more than ' + unicode(self._settings.get('threshold')) + \
            u' occurrences\n'
        desc += u'With quality\n' if quality else u'Without quality\n'
        desc += u'Size: ' + interval_size + u'\n\n'
        desc += unicode(values_of_n[0]) + u'-Gram'

        post = [(u'description', desc, u'occurrences')]
        # (5b) Add all the actual things
        for each_key in self._keys:
            post.append((each_key, self._ngrams[each_key]))

        # (6) Conclude
        return post


class LilyPondExperiment(Experiment):
    """
    Help prepare a Score for output in LilyPond syntax.

    This Experiment must be connected to the LilyPondDisplay Visualization.
    """

    # List of strings that are the names of the Display objects suitable for this Experiment
    _good_for = ['LilyPondDisplay']

    def __init__(self, controller, records, settings):
        """
        Create a new LilyPondExperiment.

        There are three mandatory arguments:
        - controller : the Experimenter object to which this Experiment belongs
        - records : a list of AnalysisRecord objects
        - settings : an ExperimentSettings object

        If there is a 'lilypond helper' setting, that experiment will be used to help produce
        meaningful output for an annotated score:
        - IntervalNGramStatistics : Produces "interval n-gram summary output," in which case only
            one score will be produced, based on all the AnalysisRecord objects received.
        - IntervalsList : Produces a score with vertical interval annotations, in which case a new
            score will be produced for every AnalysisRecord object received.
        - no setting : Produces an un-annotated score, in which case a new score will be produced
            for every new pathname in the AnalysisRecord objects received.
        """
        super(LilyPondExperiment, self).__init__(controller, records, settings)

    def perform(self):
        """
        Perform the Experiment. This method is not called "run" to avoid possible
        confusion with the multiprocessing nature of Experiment subclasses.

        This method emits an Experimenter.experimented signal when it finishes.
        """
        post = []
        if self._settings.has('lilypond helper'):
            # choose the helper experiment
            which_helper = self._settings.get('lilypond helper')
            TheHelper = None
            if 'IntervalsLists' == which_helper:
                TheHelper = TargetedIntervalNGramExperiment if self._settings.has('annotate these')\
                    else IntervalsLists
            elif 'ChordsList' == which_helper or 'ChordsLists' == which_helper:
                TheHelper = ChordsLists

            # run the experiments
            all_the_scores = []
            for each_record in self._records:
                this_result = TheHelper(self._controller, [each_record], self._settings)
                this_result = this_result.perform()
                if 'ChordsList' == which_helper:
                    this_result = LilyPondExperiment._accidental_replacer(this_result)
                # START DEBUGGING
                #asdf = LilyPondExperiment.make_ngram_score(each_record, this_result, [2])
                #print(u'================================================================')
                #print(u'================================================================')
                #print(OutputLilyPond.process_score(asdf.parts[-1]))
                #print(u'================================================================')
                #print(u'================================================================')
                #all_the_scores.append(asdf)
                # END DEBUGGING
                all_the_scores.append(LilyPondExperiment.make_ngram_score(
                    each_record, this_result, [2]))
            for each_score in all_the_scores:
                post.append(OutputLilyPond.process_score(each_score))
        else:  # just output scores
            score_paths = []
            for rec in self._records:
                score_paths.append(rec._pathname)
            scores = []
            for path in score_paths:
                scores.append(converter.parse(path))
            for each_score in scores:
                post.append(OutputLilyPond.process_score(each_score))
        return post

    @staticmethod
    def _accidental_replacer(source):
        # TODO: this must be tested
        """
        Replace accidental symbols in chord labels from the ChordsLists Experiment. In the 0th
        element of the 3-tuple, each 'b' is replaced with the LilyPond code to make a flat sign,
        and each '#' is replaced with the code to make a sharp sign.

        Parameters
        ----------

        source : list of 3-tuples
            The output from a ChordsLists Experiment.

        Returns
        -------

        list of 3-tuples
            With 'b' and '#' symbols removed and replaced, as described above and below.

        Side Effects
        ------------

        Transforms...
            [('Ab6', 'asdf', 0.5)]
        ... into...
            [('A" \flat "6', 'asdf', 0.5)]
        ... and...
            [('A#6', 'asdf', 0.5)]
        ... into...
            [('A" \sharp "6', 'asdf', 0.5)]
        """
        post = []
        for each in source:
            left, middle, right = each
            new_left = u''
            for char in left:
                if u'b' == char:
                    new_left += u'" \\raise #0.5 {\\fontsize #-4 \\flat} "'
                elif u'#' == char:
                    new_left += u'" \\raise # 0.5 {\\fontsize #-4 \\sharp} "'
                else:
                    new_left += char
            post.append((new_left, middle, right))
        return post

    @staticmethod
    def fill_space_between_offsets(start_o, end_o):
        """
        Given two float numbers, finds the quarterLength durations required to make
        the two objects viable. Assumes there is a Note starting both at the "start"
        and "end" offset.

        Returns a 2-tuplet, where the first index is the required quarterLength of
        the Note at offset start_o, and the second index is a list of the required
        quarterLength values for a series of Rest objects that fill space to the
        end_o. Ideally the list will be empty and no Rest objects will be required.

        The algorithm tries to fill the entire offset range with a single Note that
        starts at start_o, up to a maximum quarterLength of 4.0 (to avoid LilyPond
        duration representations longer than one character). The algorithm prefers
        multiple durations over a single dotted duration.
        """
        def highest_valid_ql(rem):
            """
            Returns the largest quarterLength that is less "rem" but not greater than 2.0
            """
            # Holds the valid quarterLength durations from whole note to 256th.
            list_of_durations = [2.0, 1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0]
            # Easy terminal condition
            if rem in list_of_durations:
                return rem
            # Otherwise, we have to look around
            for dur in list_of_durations:
                if dur < rem:
                    return dur

        def the_solver(ql_remains):
            """
            Given the "quarterLength that remains to be dealt with," this method returns
            the solution.
            """
            if 4.0 == ql_remains:
                # Terminal condition, just return!
                return [4.0]
            elif 4.0 > ql_remains >= 0.0:
                if 0.015625 > ql_remains:
                    # give up... ?
                    return [ql_remains]
                else:
                    possible_finish = highest_valid_ql(ql_remains)
                    if possible_finish == ql_remains:
                        return [ql_remains]
                    else:
                        return [possible_finish] + \
                        the_solver(ql_remains - possible_finish)
            elif ql_remains > 4.0:
                return [4.0] + the_solver(ql_remains - 4.0)
            else:
                msg = u'Impossible quarterLength remaining: ' + unicode(ql_remains) + \
                    u'... we started with ' + unicode(start_o) + u' to ' + unicode(end_o)
                raise RuntimeError(msg)

        start_o = float(start_o)
        end_o = float(end_o)
        result = the_solver(end_o - start_o)
        return (result[0], result[1:])

    @staticmethod
    def make_summary_score():
        """
        Given the result of an IntervalNGramStatistics Experiment, produce a "summary score."

        Returns
        -------

        music21.stream.Score
            A score that should be given to OutputLilyPond.
        """
        pass

    @staticmethod
    def make_ngram_score(record, results, list_of_enns, annotate_these=None):
        """
        Annotate a score by indicating n-grams.

        Parameters
        ----------

        record : vis.models.analyzing.AnalysisRecord
            The AnalysisRecord for the voice pair to be annotated onto its corresponding score.
            This is used for its metadata.

        results : output from IntervalsLists Experiment
            Holds the specifications of what to annotate intervals, along with the offset in the
            score. It should be a list of 3-tuples, like this:
                [(vertical_event, following_horizontal, offset_of_vertical),
                 (vertical_event, following_horizotanl, offset_of_vertical)]

        list_of_enns : list of int
            A list of the values for 'n' when finding interval n-grams.

        annotate_these : list of 2-tuples: (string, string)
            This optional argument is a list of 2-tuples that specify which interval n-grams
            should be marked in the score. For each tuple, the n-gram you want to match should
            be == the string at index 0, and the annotation colour should be the other string.
            **** NOTE: this is currently ignored

        Returns
        -------

        music21.stream.Score
            An annotated version of the inputted Score.

        # TODO: should we deepcopy() the Score before we start?
        """
        # Setup: This is the LilyPond code to be put around the object's descriptions...
        #    left_vert + vertical_event + right_vert
        #    left_horiz + horizontal_event + right_horiz
        first_left_vert = u'^\\markup{ \\right-align{\\concat{ "'
        left_vert = u'^\\markup{ \\center-align{\\concat{ "'
        right_vert = u'" }}}'
        left_horiz = u'_\\markup{ \\center-align{ "'
        right_horiz = u'" }}'

        # 0.) Check to make sure the first things in the results aren't strings for field names
        if isinstance(results[0][0], str) and isinstance(results[0][0], str):
            results = results[1:]

        # 1.) Make an analysis part for the score
        new_part = stream.Part()
        new_part.lily_analysis_voice = True
        new_part.lily_instruction = u'\t\\textLengthOn\n'

        # 1.5) Maybe the first item in "results" is descriptions of fields?
        if u'offset' == results[0][2]:
            results = results[1:]

        # 2.) Since the annotations may not begin at the start of the score, let's add some
        #     rests if we need them
        if results[0][2] > 0.0:
            needed_qls = LilyPondExperiment.fill_space_between_offsets(0.0, results[0][2])
            new_part.append(note.Rest(quarterLength=needed_qls[0]))
            for each_ql in needed_qls[1]:
                new_part.append(note.Rest(quarterLength=each_ql))

        # 3.) Add the first annotation (i.e., part names and the first vertical & horizontal event)
        the_lily = first_left_vert
        for each_name in record._part_names:
            the_lily += each_name + u' and '
        # remove the final " and "
        the_lily = the_lily[:-5] + u': '
        # add the first vertical annotation
        the_lily += unicode(results[0][0]) + right_vert
        # make and add a Note for the vertical annotation
        the_note = note.Note('C4')  # pitch doesn't matter
        the_note.lily_markup = the_lily
        new_part.insert(results[0][2], the_note)
        # we won't need this any more, but we may need the memory... ?
        del the_lily
        # figure out the offset of this horizontal thing
        horiz_offset = None
        try:
            # the results[1][2] call would raise IndexError if there's only one vertical event
            half_dist = (results[1][2] - results[0][2]) / 2.0
            horiz_offset = half_dist + results[0][2]
            new_part[-1].quarterLength = half_dist
        except IndexError:
            horiz_offset = results[0][2] + 0.5
            new_part[-1].quarterLength = 0.5
        # make annotation, then make and add the Note
        the_note = note.Note('C4')
        the_note.lily_markup = left_horiz + unicode(results[0][1]) + right_horiz
        new_part.insert(horiz_offset, the_note)

        # 4.) Add the rest of the annotations
        # remove the first element so the iterator works more easily
        results = results[1:]
        for i in xrange(len(results)):
            # 6.1) Figure out what's required to fill the space between the previous and this
            needed_qls = LilyPondExperiment.fill_space_between_offsets(new_part[-1].offset,
                results[i][2])
            # 6.2) Set the previous annotation note to the right quarterLength
            new_part[-1].quarterLength = needed_qls[0]
            # 6.3) Fill the remaining space with Rest objects, as needed
            for each_ql in needed_qls[1]:
                new_part.append(note.Rest(quarterLength=each_ql))
            # 6.4) Make the annotation then Note for this vertical interval
            the_note = note.Note('C4')
            the_note.lily_markup = left_vert + unicode(results[i][0]) + right_vert
            new_part.insert(results[i][2], the_note)
            # 6.5) Make this horizontal interval
            horiz_offset = None
            try:
                horiz_offset = ((results[i + 1][2] - results[i][2]) / 2.0) + results[i][2]
            except IndexError:
                horiz_offset = results[i][2] + 0.5
            needed_qls = LilyPondExperiment.fill_space_between_offsets(new_part[-1].offset,
                horiz_offset)
            new_part[-1].quarterLength = needed_qls[0]
            for each_ql in needed_qls[1]:
                new_part.append(note.Rest(quarterLength=each_ql))
            the_note = note.Note('C4')
            the_note.lily_markup = left_horiz + unicode(results[i][1]) + right_horiz

            new_part.insert(horiz_offset, the_note)

        # 5.) Import the score we'll use
        # TODO: not assume it imports a Score... what about an Opus?
        score = converter.parse(record._pathname)

        # 6.) Add the new annotation part to the rest of the score
        score.append(new_part)

        # 7.) Done... ?
        return score


class TargetedIntervalNGramExperiment(Experiment):
    """
    Comment here.
    """

    # List of strings that are the names of the Display objects suitable for this Experiment
    _good_for = ['LilyPond']

    def __init__(self, controller, records, settings):
        """
        Create a new TargetedIntervalNGramExperiment.

        Here's a description of what this Experiment does.

        There are three mandatory arguments:
        - controller : the Experimenter object to which this Experiment belongs
        - records : a list of AnalysisRecord objects
        - settings : an ExperimentSettings object

        These settings are required:
        - quality
        - simple or compound
        - annotate these
        """
        # Check the ExperimentSettings object has the right settings
        # These are required by IntervalsStatistics
        if not settings.has('quality') or not settings.has('simple or compound'):
            msg = u'TargetedIntervalsNGram requires "quality" and "simple or compound" settings'
            controller.error.emit(msg)
            return
        if not settings.has('annotate these'):
            msg = u'TargetedIntervalsNGram requires "quality" and "simple or compound" settings'
            controller.error.emit(msg)
            return
        # Otherwise, we're good to go!
        super(TargetedIntervalNGramExperiment, self).__init__(controller, records, settings)

    def perform(self):
        #Takes an ngram entered by the user and divides it into
		#two lists: one of the vertical intervals and the other of the lower
		#voice's melodic intervals.

		#userinput is what the user would type in. The user should be prompted
		#with instructions along the lines of:
		'''Enter the N-gram you wish to search for separating each vertical
		and horizontal interval with a space and nothing else.  Unisons are equal to
		one and inverted vertical intervals as well as descending melodic intervals
		should be preceded with a minus sign.  Please only enter numbers,
		spaces, and (when necessary) minus signs.'''

		#For now dummy userinput and IntervalsLists are provided.
		#userinput = '1 2 3 -2 4 1 3'
		userinput = self._settings.get('annotate these')
		IntervalsLists = [(8, 2, 0), (6, 2, .5), (6, 3, 1), (1, 2, 1.5), (3, -2, 2), \
							(4, 1, 2.5), (3, -5, 3), (8, None, 3.5), (1, 2, 4), \(3, -2, 4.5), 
							(4, 1, 5), (3, -5, 5.5)]
		user_intervals = str.split(userinput)
		user_ngram = []
		for p in user_intervals:
			user_ngram.append(int(p))
		#note that str.split will be removed in python 3
		#Ideally  return an error message to the user here if len(user_ngram) is not an
		#odd number 3 or greater.
		ngram_size = ((len(user_ngram)+1)/2)
		#Takes the user's ngram and puts it into a list of the vertical intervals and a
		#list of the horizontal intervals.
		vertify = []
		horify = []
		for n in range (0, len(user_ngram)):
			if n % 2 == 0:
				vertify.append(user_ngram[n])
			else:
				horify.append(user_ngram[n])

		found_ngrams = []
		for t in IntervalsLists:
			spot = IntervalsLists.index(t)
			if (vertify[0] == t[0]):
				if all((horify[(w - 1)] == IntervalsLists[(spot + w - 1)][1]) \
				and (vertify[w] == IntervalsLists[(spot + w)][0]) for w in range (1, ngram_size)):
					found_ngrams.append(list(IntervalsLists[spot:(spot + ngram_size)]))
		print found_ngrams

		# use the IntervalsLists Experiment
		# return is a list of lists of 3-tuples
        pass


class ChordParser(Experiment):
    """
    Try to parse chords out of otherwise-impenetrable textures.

    The Experiment tries the events at a particular offset, then gradually adds later offsets until
    a triad or seventh chord is formed, or until reaching a certain duration away.

    It's probably best to use this with a very small offset through the Analyzer, so this
    experiment can have all the attacks possible.
    """

    # This is a helper experiment, only suitable for use by other experiments!
    _good_for = ['None']

    def __init__(self, controller, records, settings):
        """
        Create a new ChordParser Experiment.

        The ExperimentSettings instance must have the "chord parse length" property.
        """
        if not settings.has('chord parse length'):
            msg = u'ChordParser requires the "chord parse length" setting'
            controller.error.emit(msg)
            return
        super(ChordParser, self).__init__(controller, records, settings)

    def perform(self):
        """
        Perform the Experiment.
        """
        new_ars = []

        for old_ar in self._records:
            new_ar = analyzing.AnalysisRecord()

            note_dict = {}  # hold the Note objects we generate
            force_this = False  # whether to add this sonority, even if it's not "nice"
            largest_duration = self._settings.get('chord parse length')
            i = [0]  # list of the indices to check in old_ar
            max_i = len(old_ar)
            previous_i = [-1]

            while 0 == 0:
                force_this = False
                # 1.) Did we just do the last thing?
                if i[0] >= max_i:
                    break

                # 2.) Make sure we're not going backwards
                if i[0] < previous_i[0]:
                    msg = u'ChordParser started to go backwards!'
                    self._controller.error.emit(msg)
                    return None
                elif i[0] == previous_i[0] and len(i) <= len(previous_i):
                    msg = u'ChordParser is checking the same things twice!'
                    self._controller.error.emit(msg)
                    return None

                # 3.) Update the "previous"-ly checked i values
                previous_i = deepcopy(i)

                # 4.) See if we can use this set of offsets (ensure it's not all too large)
                # If not, we'll have to just use the first thing, no matter what it is.
                if i[-1] >= max_i:  # check we don't go off the end of the AnalysisRecord
                    force_this = True
                    i = [i[0]]
                elif old_ar[i[-1]][0] - old_ar[i[0]][0] > largest_duration:  # larger than wanted
                    force_this = True
                    i = [i[0]]

                # 5.) Figure out what's at this set of offsets
                this_sonority = []
                for each_i in i:
                    for each_pitch in old_ar[each_i][1]:  # TODO: add support for "each_pitch" being a list, meaning it came from a chord
                        # Using this dict, we get a significant speed-up later in Chord.__init__()
                        if 'Rest' == each_pitch:
                            continue
                        if each_pitch in note_dict:
                            this_sonority.append(note_dict[each_pitch])
                        else:
                            new_note = note.Note(each_pitch)
                            note_dict[each_pitch] = new_note
                            this_sonority.append(new_note)

                # 6.) Make the Chord
                # "p_chord" for "possible chord"
                p_chord = chord.Chord(this_sonority)
                p_chord.removeRedundantPitchNames(inPlace=True)
                names = [p.nameWithOctave for p in p_chord]  # string-wise chord repr
                prev_chord = chord.Chord('')
                if len(new_ar) > 0:
                    prev_chord = chord.Chord([note_dict[x] for x in new_ar[-1][1]])

                # 7.) See if the Chord is "nice"
                if all([p in prev_chord.pitchClasses for p in p_chord.pitchClasses]):
                    print('at ' + str(old_ar[i[0]][0]) + ', (CONTAINED NOT) ' + str(names) +
                        ' is in ' + str(new_ar[-1][1]))  # DEBUG
                    i = [i[-1] + 1]
                elif p_chord.isTriad() or p_chord.isSeventh() or force_this:
                    if len(new_ar) == 0:  # first item in the new_ar
                        new_ar.append(old_ar[i[0]][0], names)
                        print('at ' + str(old_ar[i[0]][0]) + ', appended ' + str(names))  # DEBUG
                    else:
                        if prev_chord.orderedPitchClasses != p_chord.orderedPitchClasses:
                            # then it's the same as the previous chord
                            new_ar.append(old_ar[i[0]][0], names)
                            # START DEBUG
                            print('at ' + str(old_ar[i[0]][0]) + ', appended ' + str(names))
                        else:
                            print('at ' + str(old_ar[i[0]][0]) + ', (SAME NOT) ' + str(names))
                            # END DEBUG
                    i = [i[-1] + 1]
                else:
                    print('at ' + str(old_ar[i[0]][0]) + ', NOT ' + str(names))  # DEBUG
                    i.append(i[-1] + 1)
                print('next i is ' + str(i))  # DEBUG

            # 8.) We finished a piece!
            new_ars.append(new_ar)

        # 9.) We finished all the pieces!
        return new_ars
