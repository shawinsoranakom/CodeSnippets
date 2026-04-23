def rand(environment, end, start=None, step=None, seed=None):
    if seed is None:
        r = SystemRandom()
    else:
        r = Random(seed)
    if isinstance(end, int):
        if not start:
            start = 0
        if not step:
            step = 1
        return r.randrange(start, end, step)
    elif hasattr(end, '__iter__'):
        if start or step:
            raise AnsibleFilterError('start and step can only be used with integer values')
        return r.choice(end)
    else:
        raise AnsibleFilterError('random can only be used on sequences and integers')