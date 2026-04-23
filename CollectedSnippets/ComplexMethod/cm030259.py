def nextfile(self):
        savestdout = self._savestdout
        self._savestdout = None
        if savestdout:
            sys.stdout = savestdout

        output = self._output
        self._output = None
        try:
            if output:
                output.close()
        finally:
            file = self._file
            self._file = None
            try:
                del self._readline  # restore FileInput._readline
            except AttributeError:
                pass
            try:
                if file and not self._isstdin:
                    file.close()
            finally:
                backupfilename = self._backupfilename
                self._backupfilename = None
                if backupfilename and not self._backup:
                    try: os.unlink(backupfilename)
                    except OSError: pass

                self._isstdin = False