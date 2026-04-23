def hash_params(params):
    """
    DEPRECATED
    Construct a data structure of parameters that is hashable.

    This requires changing any mutable data structures into immutable ones.
    We chose a frozenset because role parameters have to be unique.

    .. warning::  this does not handle unhashable scalars.  Two things
        mitigate that limitation:

        1) There shouldn't be any unhashable scalars specified in the yaml
        2) Our only choice would be to return an error anyway.
    """

    _display.deprecated(
        msg="The hash_params function is deprecated as its consumers have moved to internal alternatives",
        version='2.24',
        help_text='Contact the plugin author to update their code',
    )
    # Any container is unhashable if it contains unhashable items (for
    # instance, tuple() is a Hashable subclass but if it contains a dict, it
    # cannot be hashed)
    if isinstance(params, Container) and not isinstance(params, (str, bytes)):
        if isinstance(params, Mapping):
            try:
                # Optimistically hope the contents are all hashable
                new_params = frozenset(params.items())
            except TypeError:
                new_params = set()
                for k, v in params.items():
                    # Hash each entry individually
                    new_params.add((k, hash_params(v)))
                new_params = frozenset(new_params)

        elif isinstance(params, (Set, Sequence)):
            try:
                # Optimistically hope the contents are all hashable
                new_params = frozenset(params)
            except TypeError:
                new_params = set()
                for v in params:
                    # Hash each entry individually
                    new_params.add(hash_params(v))
                new_params = frozenset(new_params)
        else:
            # This is just a guess.
            new_params = frozenset(params)
        return new_params

    # Note: We do not handle unhashable scalars but our only choice would be
    # to raise an error there anyway.
    return frozenset((params,))