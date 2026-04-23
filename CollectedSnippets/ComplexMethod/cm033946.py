def changed(result):
    """ Test if task result yields changed """
    if not isinstance(result, MutableMapping):
        raise errors.AnsibleFilterError("The 'changed' test expects a dictionary")

    if 'changed' not in result:
        changed = False
        if (
            'results' in result and   # some modules return a 'results' key
            isinstance(result['results'], MutableSequence) and
            isinstance(result['results'][0], MutableMapping)
        ):
            for res in result['results']:
                if res.get('changed'):
                    changed = True
                    break
    else:
        changed = result.get('changed')

    return bool(changed)