def _get_octal_mode_from_symbolic_perms(path_stat, user, perms, use_umask, prev_mode=None):
        if prev_mode is None:
            prev_mode = stat.S_IMODE(path_stat.st_mode)
        is_directory = stat.S_ISDIR(path_stat.st_mode)
        has_x_permissions = (prev_mode & S_IXANY) > 0
        apply_X_permission = is_directory or has_x_permissions

        # Get the umask, if the 'user' part is empty, the effect is as if (a) were
        # given, but bits that are set in the umask are not affected.
        # We also need the "reversed umask" for masking
        umask = os.umask(0)
        os.umask(umask)
        rev_umask = umask ^ PERM_BITS

        # Permission bits constants documented at:
        # https://docs.python.org/3/library/stat.html#stat.S_ISUID
        if apply_X_permission:
            X_perms = {
                'u': {'X': stat.S_IXUSR},
                'g': {'X': stat.S_IXGRP},
                'o': {'X': stat.S_IXOTH},
            }
        else:
            X_perms = {
                'u': {'X': 0},
                'g': {'X': 0},
                'o': {'X': 0},
            }

        user_perms_to_modes = {
            'u': {
                'r': rev_umask & stat.S_IRUSR if use_umask else stat.S_IRUSR,
                'w': rev_umask & stat.S_IWUSR if use_umask else stat.S_IWUSR,
                'x': rev_umask & stat.S_IXUSR if use_umask else stat.S_IXUSR,
                's': stat.S_ISUID,
                't': 0,
                'u': prev_mode & stat.S_IRWXU,
                'g': (prev_mode & stat.S_IRWXG) << 3,
                'o': (prev_mode & stat.S_IRWXO) << 6},
            'g': {
                'r': rev_umask & stat.S_IRGRP if use_umask else stat.S_IRGRP,
                'w': rev_umask & stat.S_IWGRP if use_umask else stat.S_IWGRP,
                'x': rev_umask & stat.S_IXGRP if use_umask else stat.S_IXGRP,
                's': stat.S_ISGID,
                't': 0,
                'u': (prev_mode & stat.S_IRWXU) >> 3,
                'g': prev_mode & stat.S_IRWXG,
                'o': (prev_mode & stat.S_IRWXO) << 3},
            'o': {
                'r': rev_umask & stat.S_IROTH if use_umask else stat.S_IROTH,
                'w': rev_umask & stat.S_IWOTH if use_umask else stat.S_IWOTH,
                'x': rev_umask & stat.S_IXOTH if use_umask else stat.S_IXOTH,
                's': 0,
                't': stat.S_ISVTX,
                'u': (prev_mode & stat.S_IRWXU) >> 6,
                'g': (prev_mode & stat.S_IRWXG) >> 3,
                'o': prev_mode & stat.S_IRWXO},
        }

        # Insert X_perms into user_perms_to_modes
        for key, value in X_perms.items():
            user_perms_to_modes[key].update(value)

        def or_reduce(mode, perm):
            return mode | user_perms_to_modes[user][perm]

        return reduce(or_reduce, perms, 0)