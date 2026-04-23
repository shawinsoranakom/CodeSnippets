def _decode(self, index, endflag=0):
        """Return a (line, char) tuple of int indexes into self.data.

        This implements .index without converting the result back to a string.
        The result is constrained by the number of lines and linelengths of
        self.data. For many indexes, the result is initially (1, 0).

        The input index may have any of several possible forms:
        * line.char float: converted to 'line.char' string;
        * 'line.char' string, where line and char are decimal integers;
        * 'line.char lineend', where lineend='lineend' (and char is ignored);
        * 'line.end', where end='end' (same as above);
        * 'insert', the positions before terminal \n;
        * 'end', whose meaning depends on the endflag passed to ._endex.
        * 'sel.first' or 'sel.last', where sel is a tag -- not implemented.
        """
        if isinstance(index, (float, bytes)):
            index = str(index)
        try:
            index=index.lower()
        except AttributeError:
            raise TclError('bad text index "%s"' % index) from None

        lastline =  len(self.data) - 1  # same as number of text lines
        if index == 'insert':
            return lastline, len(self.data[lastline]) - 1
        elif index == 'end':
            return self._endex(endflag)

        line, char = index.split('.')
        line = int(line)

        # Out of bounds line becomes first or last ('end') index
        if line < 1:
            return 1, 0
        elif line > lastline:
            return self._endex(endflag)

        linelength = len(self.data[line])  -1  # position before/at \n
        if char.endswith(' lineend') or char == 'end':
            return line, linelength
            # Tk requires that ignored chars before ' lineend' be valid int
        if m := re.fullmatch(r'end-(\d*)c', char, re.A):  # Used by hyperparser.
            return line, linelength - int(m.group(1))

        # Out of bounds char becomes first or last index of line
        char = int(char)
        if char < 0:
            char = 0
        elif char > linelength:
            char = linelength
        return line, char