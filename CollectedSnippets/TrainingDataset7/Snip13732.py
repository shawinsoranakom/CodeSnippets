def printErrorList(self, flavour, errors):
        for test, err, sql_debug in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour, self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln(err)
            self.stream.writeln(self.separator2)
            self.stream.writeln(sql_debug)