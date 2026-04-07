def debug(self, error):
        self._restoreStdout()
        self.buffer = False
        exc_type, exc_value, traceback = error
        print("\nOpening PDB: %r" % exc_value)
        if PY313:
            pdb.post_mortem(exc_value)
        else:
            pdb.post_mortem(traceback)