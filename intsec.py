#! /usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         intsec.py
# Purpose:      Measures sequences of vertical intervals.
# 
# Attribution:  Based on the 'harrisonHarmony.py' module available at...
#               https://github.com/crantila/harrisonHarmony/
# 
# Copyright (C) 2012 Christopher Antila
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

import pprint

## Import required libraries
from music21 import interval # confirmed requirement
from music21 import chord # confirmed requirement
from music21 import converter # confirmed requirement
from music21 import stream # confirmed requirement
from os.path import exists as pathExists # confirmed requirement
from music21.converter import ConverterException # confirmed requirement
from music21.converter import ConverterFileException # confirmed requirement
from music21 import note # confirmed requirement

#-------------------------------------------------------------------------------
class NonsensicalInputError( Exception ):
   '''
   The error that I'm using for IntSec. This should potentially be
   replaced with more useful errors.
   '''
   def __init__( self, val ):
      self.value = val
   def __str__( self ):
      return repr( self.value )
#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------
class NGram( object ):
   '''
   Represents an n-gram. In other words, holds 'n'
   :class:`music21.interval.Interval` objects and information about the voice
   movement between them.
   '''
   ## Instance Data
   # _n
   # _listOfIntervals
   # _listOfMovements
   # _heedQuality
   def __init__( self, someIntervals, heedQuality=False ):
      '''
      Create a new n-gram when given a list of the
      :class:`music21.interval.Interval` objects that are part of the n-gram.
      
      Note that all the Interval objects must have :class:`music21.note.Note`
      objects embedded, to calculate the "distance" between adjacent
      vertical intervals.
      
      The second argument, called 'heedQuality,' determines whether to consider
      intervals with their qualities, or just their species (the number). If
      possible, when calling NGram from within a program, you should use an
      IntSecSettings instance to specify heedQuality directly, like this:
      >>> from music21 import *
      >>> from intsec import *
      >>> s = IntSecSettings()
      >>> a = interval.Interval( note.Note('C4'), note.Note('E4') )
      >>> b = interval.Interval( note.Note('D4'), note.Note('E4') )
      >>> ng = NGram( [a,b], s.parsePropertyGet( 'heedQuality' ) )
      NGram( [music21.interval.Interval( music21.note.Note('C4'), music21.note.Note('E4') ),music21.interval.Interval( music21.note.Note('D4'), music21.note.Note('E4') )], False )
      '''
      self._heedQuality = heedQuality
      self._n = len(someIntervals)
      self._listOfIntervals = someIntervals
      self._calculateMovements()
   
   # internal method
   def _calculateMovements( self ):
      # Calculates the movement of between the highest notes of adjacent
      # Interval objects, then returns a list of them.
      
      # First make sure we have a note.Note for all the vertical intervals.
      # It doesn't matter which direction the Interval is, because if there
      # is a Note in either noteStart or noteEnd, there should be a Note
      # in the other.
      for eachInterval in self._listOfIntervals:
         if not isinstance( eachInterval.noteStart, note.Note ) or \
            not isinstance( eachInterval.noteEnd, note.Note ):
            raise NonsensicalInputError( 'NGram: (At least) one of the vertical intervals doesn\'t have noteStart.' )
      
      # Now calculate a list of the Interval objects between the lowest notes.
      post = []
      for i in xrange(len(self._listOfIntervals)-1):
         # We need to choose the lower Note from both Interval objects
         firstNote = secondNote = None
         if 1 == self._listOfIntervals[i].direction:
            firstNote = self._listOfIntervals[i].noteStart
         else:
            firstNote = self._listOfIntervals[i].noteEnd
         #
         if 1 == self._listOfIntervals[i+1].direction:
            secondNote = self._listOfIntervals[i+1].noteStart
         else:
            secondNote = self._listOfIntervals[i+1].noteEnd
         
         post.append( interval.Interval( firstNote, secondNote ) )
      #
      
      self._listOfMovements = post
   #
   
   def n( self ):
      return self._n
   
   # I think we shouldn't have this method because of difficulties getting
   # different answers depending on heedQuality, and because it's not
   # going to be much different from __str__() anyway.
   #def getIntervals( self ):
      #return self._listOfIntervals
   
   def __repr__( self ):
      # TODO: re-implement this, as per the Python standard... the return
      # value should be sufficient code to re-make an == object.
      return '<' + __name__ + '.NGram ' + str(self) + '>'
   
   def stringVersion( self, simpleOrCompound='compound', heedQuality=None ):
      '''
      Return a string-format representation of this NGram object. With no
      arguments, the intervals are compound, and quality is heeded or not as
      per the setting of this NGram object.
      
      This function is called by str(intsec.NGram) so the following should be
      true of any NGram object:
      str(intsec.NGram) == NGram.stringVersion()
      '''
      # If we weren't given something, we'll take the default for this NGram.
      if None == heedQuality:
         heedQuality = self._heedQuality
      
      post = ''
      
      # for each index in _listOfIntervals
      for i in xrange(len(self._listOfIntervals)):
         # If post isn't empty, put a space between this and the previous int
         if len(post) > 0:
            post += ' '
         
         # Calculate this interval
         thisInt = None
         if 'simple' == simpleOrCompound:
            thisInt = self._listOfIntervals[i].semiSimpleName
         elif 'compound' == simpleOrCompound:
            thisInt = self._listOfIntervals[i].name
         else:
            raise NonsensicalInputError( "NGram.stringVersion(): 'simpleOrCompound' (2nd argument) must be either 'simple' or 'compound'." )
         
         # If we're ignoring quality, remove the quality.
         if not heedQuality:
            thisInt = thisInt[1:]
         
         # Append this interval
         post += thisInt
         
         # Calculate the lower-voice movement after this interval.
         thisMove = None
         try: # the last interval won't have anything
            thisMove = self._listOfMovements[i]
         except IndexError as inderr:
            pass # then just don't add it
         
         if isinstance( thisMove, interval.Interval ):
            if 1 == thisMove.direction:
               post += ' +'
            elif -1 == thisMove.direction:
               post += ' -'
            else:
               post += ' '
            
            if 'simple' == simpleOrCompound:
               zzz = thisMove.semiSimpleName
            elif 'compound' == simpleOrCompound:
               zzz = thisMove.name
            else:
               raise NonsensicalInputError( "NGram.stringVersion(): 'simpleOrCompound' (2nd argument) must be either 'simple' or 'compound'." )
            
            if not heedQuality:
               zzz = zzz[1:]
            
            post += zzz
            
            thisMove = None
         #
      
      return post
   # end stringVersion
   
   def __str__( self ):
      return self.stringVersion()
   
   def __eq__( self, other ):
      if self._heedQuality != other._heedQuality or \
         self._n != other._n or \
         len(self._listOfIntervals) != len(other._listOfIntervals): # should be same as previous line
         return False
      elif self._heedQuality: # m3 and M3 are different
         if self._listOfIntervals == other._listOfIntervals and \
            self._listOfMovements == other._listOfMovements:
            return True
         else:
            return False
      else: # m3 and M3 are equivalent
         for i in xrange(len(self._listOfIntervals)):
            l = r = None
            try:
               l = abs(int(str(self._listOfIntervals[i])[-3:-1]))
            except ValueError as emer:
               l = abs(int(str(self._listOfIntervals[i])[-2:-1]))
            #
            try:
               r = abs(int(str(other._listOfIntervals[i])[-3:-1]))
            except ValueError as emer:
               r = abs(int(str(other._listOfIntervals[i])[-2:-1]))
            #
            if l != r:
               return False
         #
         for i in xrange(len(self._listOfMovements)):
            l = r = None
            try:
               l = abs(int(str(self._listOfMovements[i])[-3:-1]))
            except ValueError as emer:
               l = abs(int(str(self._listOfMovements[i])[-2:-1]))
            #
            try:
               r = abs(int(str(other._listOfMovements[i])[-3:-1]))
            except ValueError as emer:
               r = abs(int(str(other._listOfMovements[i])[-2:-1]))
            #
            if l != r or self._listOfMovements[i].direction != other._listOfMovements[i].direction:
               return False
         #
         return True
      #
   #
   
   def __ne__( self, other ):
      return not self == other
   
#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------
class VerticalIntervalStatistics( object ):
   '''
   Holds the statistics discovered by IntSec. Currently these are:
   
   - number of occurrences of each Interval
   - number of occurrences of each n-gram
   '''
   # I suspect it's too much work to interactively try to find the
   # quality/no-quality and simple/compound version of everything whenever you
   # want to just find the number of occurrences. Instead, we'll store all four
   # versions of that information. Memory is cheap!
   
   ## Instance Data
   # _simpleIntervalDict
   # _compoundIntervalDict
   # _compoundQualityNGramsDict
   # _compoundNoQualityNGramsDict
   def __init__( self ):
      '''
      Create a new, "empty" statistics database for a piece.
      '''
      self._simpleIntervalDict = {}
      self._compoundIntervalDict = {}
      self._compoundQualityNGramsDict = [{},{},{}]
      self._compoundNoQualityNGramsDict = [{},{},{}]
   
   def __repr__( self ):
      return self.__str__( self )
   
   def __str__( self ):
      return '<VerticalIntervalStatistics about intervals and n-grams>'
   
   def addInterval( self, theInterval ):
      '''
      Adds a :class:`music21.interval.Interval` to the occurrences information.
      If given a simple interval, add that to both the table of simple and
      compound intervals. If given a compound interval, adds that to the table
      of compound intervals and the single-octave equivalent to the table of
      simple intervals.
      
      Automatically accounts for tracking quality or not.
      '''
      
      # it's a simple interval
      if theInterval.name == theInterval.semiSimpleName:
         if theInterval.name in self._simpleIntervalDict:
            self._simpleIntervalDict[theInterval.name] += 1
         else:
            self._simpleIntervalDict[theInterval.name] = 1
         
         if theInterval.name in self._compoundIntervalDict:
            self._compoundIntervalDict[theInterval.name] += 1
         else:
            self._compoundIntervalDict[theInterval.name] = 1
      # it's a compound interval
      else:
         if theInterval.semiSimpleName in self._simpleIntervalDict:
            self._simpleIntervalDict[theInterval.semiSimpleName] += 1
         else:
            self._simpleIntervalDict[theInterval.semiSimpleName] = 1
         
         if theInterval.name in self._compoundIntervalDict:
            self._compoundIntervalDict[theInterval.name] += 1
         else:
            self._compoundIntervalDict[theInterval.name] = 1
   # end addInterval()
   
   def getIntervalOccurrences( self, whichInterval, simpleOrCompound='simple' ):
      '''
      Returns the number of occurrences of a particular
      :class:`music21.interval.Interval`, either (by default) from the table
      with compound intervals, or if the second argument is 'simple' then from
      the table with simple intervals.
      
      Automatically accounts for tracking quality or not.
      '''
      # Given a species (number), finds all the occurrences of any quality.
      # The second argument should be either self._simpleIntervalDict or
      # self._compoundIntervalDict
      def findNumberOfAllQualities( species, db ):
         qualities = 'dmMPA'
         post = 0
         for quality in qualities:
            if ( quality + species ) in db:
               post += db[quality+species]
         
         return post
      ##
      
      # they're ignoring quality
      if whichInterval.isdigit():
         if 'simple' == simpleOrCompound:
            return findNumberOfAllQualities( whichInterval, self._simpleIntervalDict )
         elif 'compound' == simpleOrCompound:
            return findNumberOfAllQualities( whichInterval, self._compoundIntervalDict )
         else:
            errorstr = "VerticalIntervalStatistics.getIntervalOccurrences(): 'simpleOrCompound' must be set to either 'simple' or 'compound'"
            raise NonsensicalInputError( errorstr )
      # they're paying attention to quality
      else:
         if 'simple' == simpleOrCompound:
            if whichInterval in self._simpleIntervalDict:
               return self._simpleIntervalDict[whichInterval]
            else:
               return 0
         elif 'compound' == simpleOrCompound:
            if whichInterval in self._compoundIntervalDict:
               return self._compoundIntervalDict[whichInterval]
            else:
               return 0
         else:
            errorstr = "VerticalIntervalStatistics.getIntervalOccurrences(): 'simpleOrCompound' must be set to either 'simple' or 'compound'"
            raise NonsensicalInputError( errorstr )
   # end getIntervalOccurrences()
   
   def addNGram( self, theNGram ):
      '''
      Adds an n-gram to the occurrences information. Automatically does or does
      not track quality, depending on the settings of the inputted NGram.
      '''
      
      # If there isn't yet a dictionary for this 'n' value, then we'll have to
      # make sure there is one.
      while len(self._compoundQualityNGramsDict) <= theNGram._n:
         self._compoundQualityNGramsDict.append( {} )
         self._compoundNoQualityNGramsDict.append( {} )
      
      # self._compoundQualityNGramsDict
      zzz = theNGram.stringVersion( 'compound', True )
      if zzz in self._compoundQualityNGramsDict[theNGram._n]:
         self._compoundQualityNGramsDict[theNGram._n][zzz] += 1
      else:
         self._compoundQualityNGramsDict[theNGram._n][zzz] = 1
      # self._compoundNoQualityNGramsDict
      zzz = theNGram.stringVersion( 'compound', False )
      if zzz in self._compoundNoQualityNGramsDict[theNGram._n]:
         self._compoundNoQualityNGramsDict[theNGram._n][zzz] += 1
      else:
         self._compoundNoQualityNGramsDict[theNGram._n][zzz] = 1
   # end addNGram()
   
   def getNGramOccurrences( self, whichNGram, n ):
      '''
      Returns the number of occurrences of a particular n-gram. Currently, all
      n-grams are treated as though they have compound intervals.
      
      The first argument must be the output from either NGram.stringVersion
      or str(NGram) (which calles stringVersion() internally).
      
      The second argument is the value 'n' for the n-gram you seek.
      
      Automatically does or does not track quality, depending on the settings
      of the inputted NGram objects.
      '''
      
      # I tried to implement this in a cleaner way, predicting whether or not
      # we had a dictionary for the value of n we were given, but it didn't
      # work properly, so I implemented this. This solution is clearly not
      # very good, but at least it works.
      try:
         if whichNGram[0].isalpha(): # heedQuality
            if whichNGram in self._compoundQualityNGramsDict[n]:
               return self._compoundQualityNGramsDict[n][whichNGram]
            else:
               return 0
         else: # noQuality!
            if whichNGram in self._compoundNoQualityNGramsDict[n]:
               return self._compoundNoQualityNGramsDict[n][whichNGram]
            else:
               return 0
      except IndexError as indE:
         return 0
   # end getNGramOccurrences()
#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------
def intervalSorter( x, y ):
   '''
   Returns -1 if the first argument is a smaller interval.
   Returns 1 if the second argument is a smaller interval.
   Returns 0 if both arguments are the same.
   
   Input should be a str of the following form:
   - d, m, M, or A
   - an int
   
   Examples:
   >>> from intsec import intervalSorter
   >>> intervalSorter( 'm3', 'm3' )
   0
   >>> intervalSorter( 'm3', 'M3' )
   1
   >>> intervalSorter( 'A4', 'd4' )
   -1
   '''
   if x == y:
      return 0
   elif int(x[1:]) < int(y[1:]): # if x is generically smaller
      return -1
   elif int(x[1:]) > int(y[1:]): # if y is generically smaller
      return 1
   else: # otherwise, we're down to the species/quality
      xQual = x[0]
      yQual = y[0]
      if xQual == 'd':
         return -1
      elif yQual == 'd':
         return 1
      elif xQual == 'A':
         return 1
      elif yQual == 'A':
         return -1
      elif xQual == 'm':
         return -1
      elif yQual == 'm':
         return 1
      else:
         return 0
#-------------------------------------------------------------------------------



#------------------------------------------------------------------------------
def visTheseParts( theseParts, theSettings, theStatistics ):
   # NB: I broke this into a function so it would be unit test-able.
   '''
   Given a list of two :class:`music21.stream.Part` objects, an IntSecSettings
   object, and a VerticalIntervalStatistics object, calculate the n-grams
   specified in the settings object, then put the statistics in the statistics
   object.
   
   Note that the parts must be specified so the higher part has index 0, and
   the lower part has index 1.
   '''
   
   n = 2 # TODO: get this from settings
   # TODO: Make it so that, if we get a List of integers from settings, we
   # can process the whole list.
   
   # now we'll take just the notes
   # hfn stands for "higher.flat.notes"
   hfn, lfn = theseParts[0].flat.notes, theseParts[1].flat.notes
   highestOffset = max(hfn.highestOffset, lfn.highestOffset)
   thisOffset = 0.0
   offsetInterval = 0.5 # TODO: get this from settings
   mostRecentHigh = mostRecentLow = None
   previousHighs = []
   previousLows = []
   
   while thisOffset <= highestOffset:
      # For a situation like a melisma, we need to cause the static
      # voice to update its record of previous positions, or else
      # it will seem as though every n-gram has the moving voice
      # correctly, but the static voice always has the notes leading up to
      # the start of the period of inactivity.
      lowMustUpdate = highMustUpdate = False
      # But we also need to make sure that we're not updating a part that was
      # already updated.
      lowUpdated = highUpdated = False
      
      # If thisOffset has a Note associated, assign it. But we shouldn't
      # bother with it if these Note objects actually have the same pitch
      # as the previous Note objects.
      # NOTE: This currently only
      # accounts for 2-grams, and will need substantial refactoring to deal
      # well with n of an arbitrary value.
      if len(lfn.getElementsByOffset( thisOffset )) > 0:
         # hold the Note at this offset
         lfnGEBO = lfn.getElementsByOffset( thisOffset )[0]
         # Check that this Note and the previous Note don't have the same
         # pitch class.
         if not isinstance( mostRecentLow, note.Note ) or \
                  lfnGEBO.pitch != mostRecentLow.pitch:
            # Set the previous to this, if it isn't None
            if None != mostRecentLow:
               previousLows.append( mostRecentLow )
            # set this to this
            mostRecentLow = lfnGEBO
            # set that other part must update and that we already did
            highMustUpdate = lowUpdated = True
      if len(hfn.getElementsByOffset( thisOffset )) > 0:
         # hold the Note at this offset
         hfnGEBO = hfn.getElementsByOffset( thisOffset )[0]
         # Check that this Note and the previous Note don't have the same
         # pitch class.
         if not isinstance( mostRecentHigh, note.Note ) or \
                  hfnGEBO.pitch != mostRecentHigh.pitch:
            # Set the previous to this, if it isn't None
            if None != mostRecentHigh:
               previousHighs.append( mostRecentHigh )
            # set this to this
            mostRecentHigh = hfnGEBO
            # set that other part must update and that we already did
            lowMustUpdate = highUpdated = True
      if lowMustUpdate and not lowUpdated:
         if None != mostRecentLow:
            previousLows.append( mostRecentLow )
      if highMustUpdate and not highUpdated:
         if None != mostRecentHigh:
            previousHighs.append( mostRecentHigh )
      
      # If one of the voices was updated, we haven't yet counted this
      # vertical interval.
      if lowUpdated or highUpdated:
         # count this Interval
         thisInterval = interval.Interval( mostRecentLow, mostRecentHigh )
         theStatistics.addInterval( thisInterval )
         # Count this n-gram, but make sure that there's enough previously-
         # occurring stuff to fill 'n' places.
         if len(previousLows) >= (n-1) and len(previousHighs) >= (n-1):
            theStatistics.addNGram( NGram( [interval.Interval( previousLows[-1], previousHighs[-1] ), thisInterval] ) )
         else:
            pass
      else:
         # If neither offset is the same as thisOffset, then we already did
         # count this vertical interval, so we won't do it again.
         pass
      
      # finally, increment the offset
      thisOffset += offsetInterval
# End visTheseParts() -------------------------------------------------------



#-------------------------------------------------------------------------------
def analyzeThis( pathname, theSettings = None ):#, verbosity = 'concise' ):
   '''
   Given the path to a music21-supported score, imports the score, performs a
   harmonic-functional analysis, annotates the score, and displays it with show().
   
   The second argument is optional, and takes the form of a str that is either
   'concise' or 'verbose', which will be passed to `labelThisChord()`, to
   display either verbose or concise labels.
   '''
   
   if None == theSettings:
      theSettings = IntSecSettings()
   
   theStats = VerticalIntervalStatistics()
   theScore = None
   
   # See what input we have
   if isinstance( pathname, str ):
      ## get the score
      print( "Importing score to music21." )
      try:
         theScore = converter.parse( pathname )
      except ConverterException:
         raise
      except ConverterFileException:
         raise
   elif isinstance( pathname, stream.Score ):
      theScore = pathname
   else:
      raise NonsensicalInputError( "analyzeThis(): input must be str or stream.Score; received " + str(type(pathname)) )
   
   # find out which 2 parts to investigate
   numberOfParts = len(theScore.parts)
   lookAtParts = [numberOfParts+5,numberOfParts+5]
   while lookAtParts[0] == lookAtParts[1] or lookAtParts[0] >= numberOfParts or lookAtParts[1] >= numberOfParts:
      print( "Please input the part numbers to investigate. Possibilities include:" )
      # print something like "1 for Soprano"
      for i in xrange(numberOfParts):
         print( str(i) + " for " + theScore.parts[i][0].bestName() )
      theirSpecification = raw_input( "Specify with higher part first, (e.g.) like this: 1 and 3\n--> " )
      try:
         lookAtParts[0] = int(theirSpecification[0])
         lookAtParts[1] = int(theirSpecification[-1])
      except ValueError as valErr:
         # if something didn't work out with int()
         lookAtParts = [numberOfParts+5,numberOfParts+5]
   
   # must have taken the numbers!
   higher, lower = theScore.parts[lookAtParts[0]], theScore.parts[lookAtParts[1]]
   print( "We'll use " + higher[0].bestName() + ' and ' + lower[0].bestName() + ', okay!\n' )
   
   # find out what or which 'n' to look for
   print( "In the future, we'll ask which 'n' values to look for... for now it's just 2-grams.\n" )
   n = 2
   
   print( "Processing...\n" )
   visTheseParts( [higher,lower], theSettings, theStats )
   
   print( '-----------------------' )
   print( "Here are the intervals!" )
   print( "Compound Intervals:" )
   pprint.pprint( theStats._compoundIntervalDict )
   #pprint.pprint( sorted( theStats._compoundIntervalDict.items(), cmp=intervalSorter ) )
   #print( '-----------------------' )
   #print( "Those as Simple Intervals:" )
   #pprint.pprint( theStats._simpleIntervalDict )
   #pprint.pprint( sorted( theStats._simpleIntervalDict.items(), cmp=intervalSorter ) )
   
   print( "---------------------" )
   print( "Here are the n-grams!" )
   #pprint.pprint( theStats._compoundQualityNGramsDict )
   pprint.pprint( theStats._compoundNoQualityNGramsDict )
   
   if theSettings.parsePropertyGet( 'produceLabeledScore' ):
      print( "-----------------------------" )
      print( "Processing score for display." )
      theChords.show()
   else:
      print( "------------------------------" )
      print( "Not producing annotated score." )
# End function analyzeThis() ---------------------------------------------------



# Class: IntSecSettings ----------------------------------------------
class IntSecSettings:
   # An internal class that holds settings for stuff.
   # 
   # produceLabeledScore : whether to produce a score showing interval
   #     sequences, through LilyPond.
   # heedQuality : whether to pay attention to the quality of an interval
   # 
   # NOTE: When you add a property, remember to test its default setting in
   # the unit test file.
   def __init__( self ):
      self._secretSettingsHash = {}
      self._secretSettingsHash['produceLabeledScore'] = False
      self._secretSettingsHash['heedQuality'] = False
      self._secretSettingsHash['lookForTheseNs'] = [2]
   
   def parsePropertySet( self, propertyStr ):
      # Parses 'propertyStr' and sets the specified property to the specified
      # value. Might later raise an exception if the property doesn't exist or
      # if the value is invalid.
      # 
      # Examples:
      # a.parsePropertySet( 'chordLabelVerbosity concise' )
      # a.parsePropertySet( 'set chordLabelVerbosity concise' )
      
      # just tests whether a str is 'true' or 'True' or 'false' or 'False
      def isTorF( s ):
         if 'true' == s or 'True' == s or 'false' == s or 'False' == s:
            return True
         else:
            return False
      ####
      
      # if the str starts with "set " then remove that
      if len(propertyStr) < 4:
         pass # panic
      elif 'set ' == propertyStr[:4]:
         propertyStr = propertyStr[4:]
      
      # check to make sure there's a property and a value
      spaceIndex = propertyStr.find(' ')
      if -1 == spaceIndex:
         pass #panic
      
      # make sure we have a proper 'true' or 'false' str if we need one
      if 'heedQuality' == propertyStr[:spaceIndex] or \
         'produceLabeledScore' == propertyStr[:spaceIndex] or \
         'produceLabelledScore' == propertyStr[:spaceIndex]:
            if not isTorF( propertyStr[spaceIndex+1:] ):
               raise NonsensicalInputError( "Value must be either True or False, but we got " + str(propertyStr[spaceIndex+1:]) )
      
      # TODO: some sort of parsing to allow us to set 'lookForTheseNs'
      
      # now match the property
      if propertyStr[:spaceIndex] in self._secretSettingsHash:
         self._secretSettingsHash[propertyStr[:spaceIndex]] = propertyStr[spaceIndex+1:]
      elif 'produceLabelledScore' == propertyStr[:spaceIndex]:
         self._secretSettingsHash['produceLabeledScore'] = propertyStr[spaceIndex+1:]
      # unrecognized property
      else:
         raise NonsensicalInputError( "Unrecognized property: " + propertyStr[:spaceIndex])
   
   def parsePropertyGet( self, propertyStr ):
      # Parses 'propertyStr' and returns the value of the specified property.
      # Might later raise an exception if the property doesn't exist.
      # 
      # Examples:
      # a.parsePropertyGet( 'chordLabelVerbosity' )
      # a.parsePropertyGet( 'get chordLabelVerbosity' )
      
      # if the str starts with "get " then remove that
      if len(propertyStr) < 4:
         pass # panic
      elif 'get ' == propertyStr[:4]:
         propertyStr = propertyStr[4:]
      
      # now match the property
      post = None
      if propertyStr in self._secretSettingsHash:
         post = self._secretSettingsHash[propertyStr]
      elif 'produceLabelledScore' == propertyStr:
         post = self._secretSettingsHash['produceLabeledScore']
      # unrecognized property
      else:
         raise NonsensicalInputError( "Unrecognized property: " + propertyStr )
      
      if 'True' == post or 'true' == post:
         return True
      elif 'False' == post or 'false' == post:
         return False
      else:
         return post
# End Class: IntSecSettings ------------------------------------------



# "main" function --------------------------------------------------------------
# TODO: write the GPL-specified blurb here, and implemenet the commands, as specified at the end of the licence
if __name__ == '__main__':
   print( "IntSec" )
   print( "======" )
   print( "IntSec Copyright (C) 2012 Christopher Antila" )
   print( "This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'." )
   print( "This is free software, and you are welcome to redistribute it" )
   print( "under certain conditions; type `show c' for details." )
   print( "" )
   #print( "====================================================" )
   print( "For a list of commands, type \"help\"." )
   
   mySettings = IntSecSettings()
   exitProgram = False
   
   # See which command they wanted
   while False == exitProgram:
      userSays = raw_input( "intsec @: " )
      # help
      if 'help' == userSays:
         print( "\nList of Commands:" )
         print( "-----------------" )
         print( "- 'exit' or 'quit' to exit or quit the program" )
         print( "- 'set' to set an option (see 'set help' for more information)" )
         print( "- 'get' to get the setting of an option (see 'get help')" )
         print( "" )
      elif 'exit' == userSays or 'quit' == userSays:
         print( "" )
         exitProgram = True
      # multi-word commands
      elif 0 < userSays.find(' '):
         if 'set' == userSays[:userSays.find(' ')]:
            if 'set help' == userSays:
               print( 'TODO: print set help' )
            else:
               try:
                  mySettings.parsePropertySet( userSays )
               except NonsensicalInputError as e:
                  print( "Error: " + str(e) )
         elif 'get' == userSays[:userSays.find(' ')]:
            if 'get help' == userSays:
               print( 'TODO: print get help' )
            else:
               try:
                  val = mySettings.parsePropertyGet( userSays )
                  print( val )
               except NonsensiclaInputError as e:
                  print( "Error: " + str(e) )
      else:
         if pathExists( userSays ):
            print( "Loading " + userSays + " for analysis." )
            try:
               analyzeThis( userSays, mySettings )
            except ConverterException as e:
               print( "--> musc21 Error: " + str(e) )
            except ConverterFileException as e:
               print( "--> musc21 Error: " + str(e) )
            except NonsensicalInputError as e:
               print( "--> Error from analyzeThis(): " + str(e) )
         else:
            print( "File doesn't seem to exist (" + userSays + ")" )
# End "main" function ----------------------------------------------------------