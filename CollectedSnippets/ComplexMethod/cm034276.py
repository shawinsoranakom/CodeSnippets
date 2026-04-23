def to_safe_group_name(name, replacer="_", force=False, silent=False):
    # Converts 'bad' characters in a string to underscores (or provided replacer) so they can be used as Ansible hosts or groups

    warn = ''
    if name:  # when deserializing we might not have name yet
        invalid_chars = C.INVALID_VARIABLE_NAMES.findall(name)
        if invalid_chars:
            msg = 'invalid character(s) "%s" in group name (%s)' % (to_text(set(invalid_chars)), to_text(name))
            if C.TRANSFORM_INVALID_GROUP_CHARS not in ('never', 'ignore') or force:
                name = C.INVALID_VARIABLE_NAMES.sub(replacer, name)
                if not (silent or C.TRANSFORM_INVALID_GROUP_CHARS == 'silently'):
                    display.vvvv('Replacing ' + msg)
                    warn = 'Invalid characters were found in group names and automatically replaced, use -vvvv to see details'
            else:
                if C.TRANSFORM_INVALID_GROUP_CHARS == 'never':
                    display.vvvv('Not replacing %s' % msg)
                    warn = 'Invalid characters were found in group names but not replaced, use -vvvv to see details'

    if warn:
        display.warning(warn)

    return name