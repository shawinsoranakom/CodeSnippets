def log_match(group, m, depth_before=None, depth_after=None):
    from . import _logger

    if m is not None:
        text = m.group(0)
        if text.startswith(('(', ')')) or text.endswith(('(', ')')):
            _logger.debug(f'matched <{group}> ({text!r})')
        else:
            _logger.debug(f'matched <{group}> ({text})')

    elif depth_before is not None or depth_after is not None:
        if depth_before is None:
            depth_before = '???'
        elif depth_after is None:
            depth_after = '???'
        _logger.log(1, f'depth: %s -> %s', depth_before, depth_after)

    else:
        raise NotImplementedError('this should not have been hit')