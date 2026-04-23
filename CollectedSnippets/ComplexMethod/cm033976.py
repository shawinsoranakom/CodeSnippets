def _get_diff(self, difflist):

        if not isinstance(difflist, list):
            difflist = [difflist]

        ret = []
        for diff in difflist:
            if 'dst_binary' in diff:
                ret.append(u"diff skipped: destination file appears to be binary\n")
            if 'src_binary' in diff:
                ret.append(u"diff skipped: source file appears to be binary\n")
            if 'dst_larger' in diff:
                ret.append(u"diff skipped: destination file size is greater than %d\n" % diff['dst_larger'])
            if 'src_larger' in diff:
                ret.append(u"diff skipped: source file size is greater than %d\n" % diff['src_larger'])
            if 'before' in diff and 'after' in diff:
                # format complex structures into 'files'
                for x in ['before', 'after']:
                    if isinstance(diff[x], _c.Mapping):
                        diff[x] = self._serialize_diff(diff[x])
                    elif diff[x] is None:
                        diff[x] = ''
                if 'before_header' in diff:
                    before_header = u"before: %s" % diff['before_header']
                else:
                    before_header = u'before'
                if 'after_header' in diff:
                    after_header = u"after: %s" % diff['after_header']
                else:
                    after_header = u'after'
                before_lines = diff['before'].splitlines(True)
                after_lines = diff['after'].splitlines(True)
                if before_lines and not before_lines[-1].endswith(u'\n'):
                    before_lines[-1] += u'\n\\ No newline at end of file\n'
                if after_lines and not after_lines[-1].endswith('\n'):
                    after_lines[-1] += u'\n\\ No newline at end of file\n'
                differ = difflib.unified_diff(before_lines,
                                              after_lines,
                                              fromfile=before_header,
                                              tofile=after_header,
                                              fromfiledate=u'',
                                              tofiledate=u'',
                                              n=C.DIFF_CONTEXT)
                difflines = list(differ)
                has_diff = False
                for line in difflines:
                    has_diff = True
                    if line.startswith(u'+'):
                        line = stringc(line, C.COLOR_DIFF_ADD)
                    elif line.startswith(u'-'):
                        line = stringc(line, C.COLOR_DIFF_REMOVE)
                    elif line.startswith(u'@@'):
                        line = stringc(line, C.COLOR_DIFF_LINES)
                    ret.append(line)
                if has_diff:
                    ret.append('\n')
            if 'prepared' in diff:
                ret.append(diff['prepared'])
        return u''.join(ret)