def get_sysctl(module, prefixes):

    sysctl = dict()
    sysctl_cmd = module.get_bin_path('sysctl')
    if sysctl_cmd is not None:

        cmd = [sysctl_cmd]
        cmd.extend(prefixes)

        try:
            rc, out, err = module.run_command(cmd)
        except OSError as ex:
            module.error_as_warning('Unable to read sysctl.', exception=ex)
            rc = 1

        if rc == 0:
            key = ''
            value = ''
            for line in out.splitlines():
                if not line.strip():
                    continue

                if line.startswith(' '):
                    # handle multiline values, they will not have a starting key
                    # Add the newline back in so people can split on it to parse
                    # lines if they need to.
                    value += '\n' + line
                    continue

                if key:
                    sysctl[key] = value.strip()

                try:
                    (key, value) = re.split(r'\s?=\s?|: ', line, maxsplit=1)
                except Exception as ex:
                    module.error_as_warning(f'Unable to split sysctl line {line!r}.', exception=ex)

            if key:
                sysctl[key] = value.strip()

    return sysctl