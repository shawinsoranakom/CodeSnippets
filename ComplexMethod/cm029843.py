def _read_inner(self, fp, fpname):
        st = _ReadState()

        for st.lineno, line in enumerate(map(self._comments.wrap, fp), start=1):
            if not line.clean:
                if self._empty_lines_in_values:
                    # add empty line to the value, but only if there was no
                    # comment on the line
                    if (not line.has_comments and
                        st.cursect is not None and
                        st.optname and
                        st.cursect[st.optname] is not None):
                        st.cursect[st.optname].append('') # newlines added at join
                else:
                    # empty line marks end of value
                    st.indent_level = sys.maxsize
                continue

            first_nonspace = self.NONSPACECRE.search(line)
            st.cur_indent_level = first_nonspace.start() if first_nonspace else 0

            if self._handle_continuation_line(st, line, fpname):
                continue

            self._handle_rest(st, line, fpname)

        return st.errors