def _printDurations(self, result):
        if not result.collectedDurations:
            return
        ls = sorted(result.collectedDurations, key=lambda x: x[1],
                    reverse=True)
        if self.durations > 0:
            ls = ls[:self.durations]
        self.stream.writeln("Slowest test durations")
        if hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)
        hidden = False
        for test, elapsed in ls:
            if self.verbosity < 2 and elapsed < 0.001:
                hidden = True
                continue
            self.stream.writeln("%-10s %s" % ("%.3fs" % elapsed, test))
        if hidden:
            self.stream.writeln("\n(durations < 0.001s were hidden; "
                                "use -v to show these durations)")
        else:
            self.stream.writeln("")