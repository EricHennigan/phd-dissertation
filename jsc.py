#!/usr/bin/env python

from subprocess import Popen, PIPE
import tempfile

JSC_EXEC="/mnt/array/projects/jsflow-webkit/web1-uci/WebKitBuild/Debug/JavaScriptCore/jsc"

class jsc(object):
  def __init__(self, code):
    self.tmpjs = tempfile.NamedTemporaryFile()
    self.tmpjs.file.write(code)
    self.tmpjs.file.flush()

  def run(self):
    p = Popen([JSC_EXEC, self.tmpjs.name], stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
    self.output = [s.replace(self.tmpjs.name, 'Interpreter') for s in p.stdout.readlines()]

  def instructions(self):
    if not self.output:
      self.run()

    buf = []
    for line in self.output:
      sline = line.rstrip()
      if sline == 'Identifiers:':
        break
      buf.append(line)

    return buf[2:-1]


if __name__ == "__main__":
  import sys
  code = open(sys.argv[1], 'r').read()
  js = jsc(code)
  js.run()
  print js.instructions()
