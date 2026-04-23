def _search_regex(self, pattern, string, name, default=NO_DEFAULT, fatal=True, flags=0, group=None):
        """
        Perform a regex search on the given string, using a single or a list of
        patterns returning the first matching group.
        In case of failure return a default value or raise a WARNING or a
        RegexNotFoundError, depending on fatal, specifying the field name.
        """
        if string is None:
            mobj = None
        elif isinstance(pattern, (str, re.Pattern)):
            mobj = re.search(pattern, string, flags)
        else:
            for p in pattern:
                mobj = re.search(p, string, flags)
                if mobj:
                    break

        _name = self._downloader._format_err(name, self._downloader.Styles.EMPHASIS)

        if mobj:
            if group is None:
                # return the first matching group
                return next(g for g in mobj.groups() if g is not None)
            elif isinstance(group, (list, tuple)):
                return tuple(mobj.group(g) for g in group)
            else:
                return mobj.group(group)
        elif default is not NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError(f'Unable to extract {_name}')
        else:
            self.report_warning(f'unable to extract {_name}' + bug_reports_message())
            return None