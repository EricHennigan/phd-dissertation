#!/usr/bin/env python

'''
changes a raw dump of bytecodes (from jsc debug function) to pretty latex
'''

import sys
import re
from optparse import OptionParser
import Queue

################
# Options
#===============
usage = "usage: %prog file"
description = __doc__
parser = OptionParser(usage=usage) #,description=description)
parser.add_option("-c", "--caption", action="store", default="",
    dest="caption", help="Set the lstlisting caption")
parser.add_option("-l", "--label", action="store", default="",
    dest="label", help="Set the lstlisting label")
################


FILENAME = ""

def getJumps(lines):
  return [getJump(x) for x in lines if getJump(x)]

def separate_blocks(lines):
  newlines = ['']
  jumptargets = [x['target'] for x in getJumps(lines)]

  for line in lines:
    if getLineNum(line) in jumptargets and newlines[-1] != '':
      newlines.append('')
    newlines.append(line)
    if getOpcodeName(line) in ['jmp', 'jfalse', 'jtrue', 'loop_if_true', 'loop_if_false']:
      newlines.append('')

  return newlines[1:]

def latex_escape(line):
  if not line:
    return line
  return line

################

def latexEscape(s):
    s = s.replace('\\', '\\textbackslash')
    s = s.replace('_', '\\_')
    s = s.replace('&', '\\&')
    s = s.replace('$', '\\$')
    return s

class CodeLine:
  """A line of JSC Bytecode dump"""
  OFFSET_PAT = re.compile('\d+')
  OPCODENAME_PAT = re.compile('[A-Za-z_]+')
  TARGET_PAT = re.compile('\(->\d+')

  def __init__(self, line):
    self.line = line.rstrip()
    self.byteOffset = int(CodeLine.OFFSET_PAT.search(self.line).group(0))
    self.opcodeName = CodeLine.OPCODENAME_PAT.search(self.line).group(0)
    self.args = self.line.split(self.opcodeName)[1].lstrip()

    self.source = self.byteOffset
    self.target = CodeLine.TARGET_PAT.search(self.line)
    if self.target:
      self.target = int(self.target.group(0)[3:])

  def __str__(self):
    return str((self.byteOffset, self.opcodeName, self.target)) + self.line

  def toNode(self, text, name=None, option=None):
    s = '\\node'
    if name:
      s += '(%s)'%name
    if option:
      s += '[%s]'%option
    s += '{%s};'%latexEscape(text)
    return s
    
  def byteOffsetStr(self):
    # 2 char wide, right aligned, fill with "0"
    return '[{0:{1}>2}]'.format(self.byteOffset, "0")

  def opcodeStr(self):
    return '{0:s}'.format(self.opcodeName)

  def argumentsStr(self):
    return '{0:s}'.format(self.args)

  def doesJump(self):
    return self.target != None

class Intervals:
  SOURCE=0
  TARGET=1
  NAME=2

  LEFT=0
  RIGHT=1

  @classmethod
  def isForward(codeline):
    if not codeline.doesJump():
      return False
    return codeline.target > codeline.byteOffset

  def __init__(self, codelines):
    self.intervals = [ [], [] ]

    for line in codelines:
       if not line.doesJump():
         continue
       interval = (line.source, line.target, line.opcodeName)
       self.intervals[self.__getSide(interval)].append(interval)

    self.intervals[Intervals.LEFT].sort()
    self.intervals[Intervals.RIGHT].sort()

  def toLatex(self):
    return self.__latexLeft() + self.__latexRight()

  def __getSide(self, interval):
    return (Intervals.LEFT,Intervals.RIGHT)[interval[Intervals.SOURCE] > interval[Intervals.TARGET]]

  def __latexLeft(self):
    paths = {}
    work = Queue.PriorityQueue()
    offset = LinearAllocator(self.intervals[Intervals.LEFT])
    registers = {}

    PRIORITY=0; ACTION=1; DATA=2
    for interval in self.intervals[Intervals.LEFT]:
      work.put( (interval[Intervals.SOURCE], offset.allocate, interval) )
      work.put( (interval[Intervals.TARGET], offset.deallocate, interval) )

    while not work.empty():
      item = work.get()
      interval = item[DATA]

      if item[ACTION] == offset.allocate:
        registers[interval] = item[ACTION](interval)
        d = {'bytecode': interval[Intervals.SOURCE],
             'register': registers[interval] + 1,
             'adjustment': '{(5pt,5pt)}'}

        paths[interval] = []
        paths[interval].append('([shift=%(adjustment)s]op%(bytecode)s.south west)'%d)
        paths[interval].append('($ ([shift=%(adjustment)s]op%(bytecode)s.south west) + (-%(register)dex,0) $)'%d)

      elif item[ACTION] == offset.deallocate:
        item[ACTION](interval)
        d = {'bytecode': interval[Intervals.TARGET],
             'register': registers[interval] + 1,
             'adjustment': '{(5pt,-5pt)}'}

        paths[interval].append('($ ([shift=%(adjustment)s]op%(bytecode)s.north west) + (-%(register)dex,0) $)'%d)
        paths[interval].append('([shift=%(adjustment)s]op%(bytecode)s.north west)'%d)

    strs = []
    for interval in self.intervals[Intervals.LEFT]:
      arrow = '\draw[->, thick]'
      arrow += ' -- '.join(paths[interval])
      arrow += ';'
      strs.append(arrow)
    return "\n".join(strs)

  def __latexRight(self):
    paths = {}
    work = Queue.PriorityQueue()
    offset = LinearAllocator(self.intervals[Intervals.RIGHT])
    registers = {}

    PRIORITY=0; ACTION=1; DATA=2
    for interval in self.intervals[Intervals.RIGHT]:
      work.put( (-interval[Intervals.SOURCE], offset.allocate, interval) )
      work.put( (-interval[Intervals.TARGET], offset.deallocate, interval) )

    while not work.empty():
      item = work.get()
      interval = item[DATA]

      if item[ACTION] == offset.allocate:
        registers[interval] = item[ACTION](interval)
        d = {'bytecode': interval[Intervals.SOURCE],
             'register': registers[interval] + 1,
             'adjustment': '{(-5pt,4pt)}'}

        """
        point1 = '(op%s.south east)'%jump[0]
        point2 = '($ (op%s.south east) + (+%dex,0) $)'%(jump[0], len(right_set))
        point3 = '($ (op%s.north east) + (+%dex,0) $)'%(jump[1], len(right_set))
        point4 = '(op%s.north east)'%jump[1]
        """
        paths[interval] = []
        paths[interval].append('([shift=%(adjustment)s]op%(bytecode)s.south east)'%d)
        paths[interval].append('($ ([shift=%(adjustment)s]op%(bytecode)s.south east) + (%(register)dex,0) $)'%d)

      elif item[ACTION] == offset.deallocate:
        item[ACTION](interval)
        d = {'bytecode': interval[Intervals.TARGET],
             'register': registers[interval] + 1,
             'adjustment': '{(-5pt,-4pt)}'}

        paths[interval].append('($ ([shift=%(adjustment)s]op%(bytecode)s.north east) + (%(register)dex,0) $)'%d)
        paths[interval].append('([shift=%(adjustment)s]op%(bytecode)s.north east)'%d)

    self.__rightShift = offset.max_allocation()

    strs = []
    for interval in self.intervals[Intervals.RIGHT]:
      arrow = '\draw[->, thick]'
      arrow += ' -- '.join(paths[interval])
      arrow += ';'
      strs.append(arrow)
    return "\n".join(strs)

  def latexRightSize(self):
    return '%dex+15pt'%self.__rightShift

class BoundaryError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)
  
class LinearAllocator:
  """Allocate things in a linear array"""

  class Nonce:
    def __nonzero__(self):
      return False
    def __eq__(self, other):
      return isinstance(other,LinearAllocator.Nonce)
  NONCE = Nonce()

  def __init__(self, things):
    self.depths = [LinearAllocator.NONCE,]*len(things)
    self.__max = 0

  def allocate(self, thing):
    for i in range(len(self.depths)):
      if self.depths[i] == LinearAllocator.NONCE:
        self.depths[i] = thing
        self.__max = max(self.__max, i)
        return i
    raise BoundaryError("Allocation array is full.")

  def deallocate(self, thing):
    for i in range(len(self.depths)):
      if self.depths[i] == thing:
        self.depths[i] = LinearAllocator.NONCE

  def max_allocation(self):
    return self.__max;

################

def tikz_picture(asmdump):

  codelines = [CodeLine(x) for x in asmdump]
  intervals = Intervals(codelines)
  # caution, to toLatex required to be called here
  #          because arrow allocation calculates latexRightSize value
  paths = intervals.toLatex()

  #print "\\resizebox{\\linewidth}{!}{"
  print "\\begin{adjustbox}{width=\\linewidth}"
  print "\\begin{tikzpicture}["
  print "   offset/.style = {font=\\color{black!50}\\ttfamily},"
  print "   opcode/.style = {font=\\ttfamily},"
  print "   args/.style = {font=\\ttfamily},"
  print "]"
  print '\\matrix ['
  print '  column 1/.style = {column sep=%s},'%intervals.latexRightSize()
  print '  column 2/.style = {anchor=west},'
  print '  column 3/.style = {anchor=west},'
  print '] {'
  for line in codelines:
    print line.toNode(line.byteOffsetStr(), option='offset', name='op%s'%line.byteOffset),
    print '&',
    print line.toNode(line.opcodeStr(), option='opcode'),
    print '&',
    print line.toNode(line.argumentsStr(), option='args'),
    print '\\\\'
  print '};'

  print paths

  print "\\end{tikzpicture}"
  print "\\end{adjustbox}"

if __name__ == "__main__":
  (options, args) = parser.parse_args()

  if len(args) != 1:
      print __doc__
      parser.print_help()
      sys.exit()

  tikz_picture(open(args[0]))
