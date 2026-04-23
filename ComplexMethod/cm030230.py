def long_has_args(opt, longopts):
    possibilities = [o for o in longopts if o.startswith(opt)]
    if not possibilities:
        raise GetoptError(_('option --%s not recognized') % opt, opt)
    # Is there an exact match?
    if opt in possibilities:
        return False, opt
    elif opt + '=' in possibilities:
        return True, opt
    elif opt + '=?' in possibilities:
        return '?', opt
    # Possibilities must be unique to be accepted
    if len(possibilities) > 1:
        raise GetoptError(
            _("option --%s not a unique prefix; possible options: %s")
            % (opt, ", ".join(possibilities)),
            opt,
        )
    assert len(possibilities) == 1
    unique_match = possibilities[0]
    if unique_match.endswith('=?'):
        return '?', unique_match[:-2]
    has_arg = unique_match.endswith('=')
    if has_arg:
        unique_match = unique_match[:-1]
    return has_arg, unique_match