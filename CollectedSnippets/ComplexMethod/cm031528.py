def grep_it(self, prog, path):
        """Search for prog within the lines of the files in path.

        For the each file in the path directory, open the file and
        search each line for the matching pattern.  If the pattern is
        found,  write the file and line information to stdout (which
        is an OutputWindow).

        Args:
            prog: The compiled, cooked search pattern.
            path: String containing the search path.
        """
        folder, filepat = os.path.split(path)
        if not folder:
            folder = os.curdir
        filelist = sorted(findfiles(folder, filepat, self.recvar.get()))
        self.close()
        pat = self.engine.getpat()
        print(f"Searching {pat!r} in {path} ...")
        hits = 0
        try:
            for fn in filelist:
                try:
                    with open(fn, errors='replace') as f:
                        for lineno, line in enumerate(f, 1):
                            if line[-1:] == '\n':
                                line = line[:-1]
                            if prog.search(line):
                                sys.stdout.write(f"{fn}: {lineno}: {line}\n")
                                hits += 1
                except OSError as msg:
                    print(msg)
            print(f"Hits found: {hits}\n(Hint: right-click to open locations.)"
                  if hits else "No hits.")
        except AttributeError:
            # Tk window has been closed, OutputWindow.text = None,
            # so in OW.write, OW.text.insert fails.
            pass