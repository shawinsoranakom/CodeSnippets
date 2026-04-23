def checksyntax(self, filename):
        self.shell = shell = self.flist.open_shell()
        saved_stream = shell.get_warning_stream()
        shell.set_warning_stream(shell.stderr)
        with open(filename, 'rb') as f:
            source = f.read()
        if b'\r' in source:
            source = source.replace(b'\r\n', b'\n')
            source = source.replace(b'\r', b'\n')
        if source and source[-1] != ord(b'\n'):
            source = source + b'\n'
        editwin = self.editwin
        text = editwin.text
        text.tag_remove("ERROR", "1.0", "end")
        try:
            # If successful, return the compiled code
            return compile(source, filename, "exec")
        except (SyntaxError, OverflowError, ValueError) as value:
            msg = getattr(value, 'msg', '') or value or "<no detail available>"
            lineno = getattr(value, 'lineno', '') or 1
            offset = getattr(value, 'offset', '') or 0
            if offset == 0:
                lineno += 1  #mark end of offending line
            pos = "0.0 + %d lines + %d chars" % (lineno-1, offset-1)
            editwin.colorize_syntax_error(text, pos)
            self.errorbox("SyntaxError", "%-20s" % msg)
            return False
        finally:
            shell.set_warning_stream(saved_stream)