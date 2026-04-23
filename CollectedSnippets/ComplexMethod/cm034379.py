def main():
    module = AnsibleModule(
        argument_spec=dict(
            paths=dict(type='list', required=True, aliases=['name', 'path'], elements='path'),
            patterns=dict(type='list', default=[], aliases=['pattern'], elements='str'),
            excludes=dict(type='list', aliases=['exclude'], elements='str'),
            contains=dict(type='str'),
            read_whole_file=dict(type='bool', default=False),
            file_type=dict(type='str', default="file", choices=['any', 'directory', 'file', 'link']),
            age=dict(type='str'),
            age_stamp=dict(type='str', default="mtime", choices=['atime', 'ctime', 'mtime']),
            size=dict(type='str'),
            recurse=dict(type='bool', default=False),
            hidden=dict(type='bool', default=False),
            follow=dict(type='bool', default=False),
            get_checksum=dict(type='bool', default=False),
            checksum_algorithm=dict(type='str', default='sha1',
                                    choices=['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'],
                                    aliases=['checksum', 'checksum_algo']),
            use_regex=dict(type='bool', default=False),
            depth=dict(type='int'),
            mode=dict(type='raw'),
            exact_mode=dict(type='bool', default=True),
            encoding=dict(type='str'),
            limit=dict(type='int')
        ),
        supports_check_mode=True,
    )

    params = module.params

    if params['mode'] and not isinstance(params['mode'], str):
        module.fail_json(
            msg="argument 'mode' is not a string and conversion is not allowed, value is of type %s" % params['mode'].__class__.__name__
        )

    # Set the default match pattern to either a match-all glob or
    # regex depending on use_regex being set.  This makes sure if you
    # set excludes: without a pattern pfilter gets something it can
    # handle.
    if not params['patterns']:
        if params['use_regex']:
            params['patterns'] = ['.*']
        else:
            params['patterns'] = ['*']

    filelist = []
    skipped = {}

    def handle_walk_errors(e):
        if e.errno in (errno.EPERM, errno.EACCES, errno.ENOENT):
            skipped[e.filename] = to_text(e)
            return
        raise e

    if params['age'] is None:
        age = None
    else:
        # convert age to seconds:
        m = re.match(r"^(-?\d+)(s|m|h|d|w)?$", params['age'].lower())
        seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        if m:
            age = int(m.group(1)) * seconds_per_unit.get(m.group(2), 1)
        else:
            module.fail_json(age=params['age'], msg="failed to process age")

    if params['size'] is None:
        size = None
    else:
        # convert size to bytes:
        m = re.match(r"^(-?\d+)(b|k|m|g|t)?$", params['size'].lower())
        bytes_per_unit = {"b": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}
        if m:
            size = int(m.group(1)) * bytes_per_unit.get(m.group(2), 1)
        else:
            module.fail_json(size=params['size'], msg="failed to process size")

    if params['limit'] is not None and params['limit'] <= 0:
        module.fail_json(msg="limit cannot be %d (use None for unlimited)" % params['limit'])

    now = time.time()
    msg = 'All paths examined'
    looked = 0
    has_warnings = False
    for npath in params['paths']:
        try:
            if not os.path.isdir(npath):
                raise Exception("'%s' is not a directory" % to_native(npath))

            # Setting `topdown=True` to explicitly guarantee matches are made from the shallowest directory first
            for root, dirs, files in os.walk(npath, onerror=handle_walk_errors, followlinks=params['follow'], topdown=True):
                looked = looked + len(files) + len(dirs)
                for fsobj in (files + dirs):
                    fsname = os.path.normpath(os.path.join(root, fsobj))
                    if params['depth']:
                        wpath = npath.rstrip(os.path.sep) + os.path.sep
                        depth = int(fsname.count(os.path.sep)) - int(wpath.count(os.path.sep)) + 1
                        if depth > params['depth']:
                            # Empty the list used by os.walk to avoid traversing deeper unnecessarily
                            del dirs[:]
                            continue
                    if os.path.basename(fsname).startswith('.') and not params['hidden']:
                        continue

                    try:
                        st = os.lstat(fsname)
                    except OSError as ex:
                        module.error_as_warning(f"Skipped entry {fsname!r} due to access issue.", exception=ex)
                        skipped[fsname] = str(ex)
                        has_warnings = True
                        continue

                    r = {'path': fsname}
                    if params['file_type'] == 'any':
                        if (pfilter(fsobj, params['patterns'], params['excludes'], params['use_regex']) and
                                agefilter(st, now, age, params['age_stamp']) and
                                mode_filter(st, params['mode'], params['exact_mode'], module)):

                            r.update(statinfo(st))
                            if stat.S_ISREG(st.st_mode) and params['get_checksum']:
                                r['checksum'] = module.digest_from_file(fsname, params['checksum_algorithm'])

                            if stat.S_ISREG(st.st_mode):
                                if sizefilter(st, size):
                                    filelist.append(r)
                            else:
                                filelist.append(r)

                    elif stat.S_ISDIR(st.st_mode) and params['file_type'] == 'directory':
                        if (pfilter(fsobj, params['patterns'], params['excludes'], params['use_regex']) and
                                agefilter(st, now, age, params['age_stamp']) and
                                mode_filter(st, params['mode'], params['exact_mode'], module)):

                            r.update(statinfo(st))
                            filelist.append(r)

                    elif stat.S_ISREG(st.st_mode) and params['file_type'] == 'file':
                        if (pfilter(fsobj, params['patterns'], params['excludes'], params['use_regex']) and
                                agefilter(st, now, age, params['age_stamp']) and
                                sizefilter(st, size) and
                                contentfilter(fsname, params['contains'], params['encoding'], params['read_whole_file']) and
                                mode_filter(st, params['mode'], params['exact_mode'], module)):

                            r.update(statinfo(st))
                            if params['get_checksum']:
                                r['checksum'] = module.digest_from_file(fsname, params['checksum_algorithm'])
                            filelist.append(r)

                    elif stat.S_ISLNK(st.st_mode) and params['file_type'] == 'link':
                        if (pfilter(fsobj, params['patterns'], params['excludes'], params['use_regex']) and
                                agefilter(st, now, age, params['age_stamp']) and
                                mode_filter(st, params['mode'], params['exact_mode'], module)):

                            r.update(statinfo(st))
                            filelist.append(r)

                    if len(filelist) == params["limit"]:
                        # Breaks out of directory files loop only
                        msg = "Limit of matches reached"
                        break

                if not params['recurse'] or len(filelist) == params["limit"]:
                    break
        except Exception as e:
            skipped[npath] = to_text(e)
            module.warn("Skipped '%s' path due to this access issue: %s\n" % (to_text(npath), skipped[npath]))
            has_warnings = True

    if has_warnings:
        msg = 'Not all paths examined, check warnings for details'
    matched = len(filelist)
    module.exit_json(files=filelist, changed=False, msg=msg, matched=matched, examined=looked, skipped_paths=skipped)