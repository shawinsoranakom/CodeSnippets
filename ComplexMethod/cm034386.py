def additional_parameter_handling(params):
    """Additional parameter validation and reformatting"""
    # When path is a directory, rewrite the pathname to be the file inside of the directory
    # TODO: Why do we exclude link?  Why don't we exclude directory?  Should we exclude touch?
    # I think this is where we want to be in the future:
    # when isdir(path):
    # if state == absent:  Remove the directory
    # if state == touch:   Touch the directory
    # if state == directory: Assert the directory is the same as the one specified
    # if state == file:    place inside of the directory (use _original_basename)
    # if state == link:    place inside of the directory (use _original_basename.  Fallback to src?)
    # if state == hard:    place inside of the directory (use _original_basename.  Fallback to src?)
    if (params['state'] not in ("link", "absent") and os.path.isdir(to_bytes(params['path'], errors='surrogate_or_strict'))):
        basename = None

        if params['_original_basename']:
            basename = params['_original_basename']
        elif params['src']:
            basename = os.path.basename(params['src'])

        if basename:
            params['path'] = os.path.join(params['path'], basename)

    # state should default to file, but since that creates many conflicts,
    # default state to 'current' when it exists.
    prev_state = get_state(to_bytes(params['path'], errors='surrogate_or_strict'))

    if params['state'] is None:
        if prev_state != 'absent':
            params['state'] = prev_state
        elif params['recurse']:
            params['state'] = 'directory'
        else:
            params['state'] = 'file'

    # make sure the target path is a directory when we're doing a recursive operation
    if params['recurse'] and params['state'] != 'directory':
        module.fail_json(
            msg="recurse option requires state to be 'directory'",
            path=params["path"]
        )

    # Fail if 'src' but no 'state' is specified
    if params['src'] and params['state'] not in ('link', 'hard'):
        module.fail_json(
            msg="src option requires state to be 'link' or 'hard'",
            path=params['path']
        )