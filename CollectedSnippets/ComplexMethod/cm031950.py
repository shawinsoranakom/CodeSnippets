def _check_mode(st, mode, check, user):
    orig = check
    _, uid, gid, groups = _get_user_info(user)
    if check & S_IRANY:
        check -= S_IRANY
        matched = False
        if mode & stat.S_IRUSR:
            if st.st_uid == uid:
                matched = True
        if mode & stat.S_IRGRP:
            if st.st_uid == gid or st.st_uid in groups:
                matched = True
        if mode & stat.S_IROTH:
            matched = True
        if not matched:
            return False
    if check & S_IWANY:
        check -= S_IWANY
        matched = False
        if mode & stat.S_IWUSR:
            if st.st_uid == uid:
                matched = True
        if mode & stat.S_IWGRP:
            if st.st_uid == gid or st.st_uid in groups:
                matched = True
        if mode & stat.S_IWOTH:
            matched = True
        if not matched:
            return False
    if check & S_IXANY:
        check -= S_IXANY
        matched = False
        if mode & stat.S_IXUSR:
            if st.st_uid == uid:
                matched = True
        if mode & stat.S_IXGRP:
            if st.st_uid == gid or st.st_uid in groups:
                matched = True
        if mode & stat.S_IXOTH:
            matched = True
        if not matched:
            return False
    if check:
        raise NotImplementedError((orig, check))
    return True