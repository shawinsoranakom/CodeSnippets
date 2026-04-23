def _symbolic_mode_to_octal(cls, path_stat, symbolic_mode):
        """
        This enables symbolic chmod string parsing as stated in the chmod man-page

        This includes things like: "u=rw-x+X,g=r-x+X,o=r-x+X"
        """

        new_mode = stat.S_IMODE(path_stat.st_mode)

        # Now parse all symbolic modes
        for mode in symbolic_mode.split(','):
            # Per single mode. This always contains a '+', '-' or '='
            # Split it on that
            permlist = MODE_OPERATOR_RE.split(mode)

            # And find all the operators
            opers = MODE_OPERATOR_RE.findall(mode)

            # The user(s) where it's all about is the first element in the
            # 'permlist' list. Take that and remove it from the list.
            # An empty user or 'a' means 'all'.
            users = permlist.pop(0)
            use_umask = (users == '')
            if users == 'a' or users == '':
                users = 'ugo'

            # Check if there are illegal characters in the user list
            # They can end up in 'users' because they are not split
            if not USERS_RE.match(users):
                raise ValueError("bad symbolic permission for mode: %s" % mode)

            # Now we have two list of equal length, one contains the requested
            # permissions and one with the corresponding operators.
            for idx, perms in enumerate(permlist):
                # Check if there are illegal characters in the permissions
                if not PERMS_RE.match(perms):
                    raise ValueError("bad symbolic permission for mode: %s" % mode)

                for user in users:
                    mode_to_apply = cls._get_octal_mode_from_symbolic_perms(path_stat, user, perms, use_umask, new_mode)
                    new_mode = cls._apply_operation_to_mode(user, opers[idx], mode_to_apply, new_mode)

        return new_mode