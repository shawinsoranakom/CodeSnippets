def transform_children(child_dict, modname=None):
    """Transform a child dictionary to an ordered sequence of objects.

    The dictionary maps names to pyclbr information objects.
    Filter out imported objects.
    Augment class names with bases.
    The insertion order of the dictionary is assumed to have been in line
    number order, so sorting is not necessary.

    The current tree only calls this once per child_dict as it saves
    TreeItems once created.  A future tree and tests might violate this,
    so a check prevents multiple in-place augmentations.
    """
    obs = []  # Use list since values should already be sorted.
    for key, obj in child_dict.items():
        if modname is None or obj.module == modname:
            if hasattr(obj, 'super') and obj.super and obj.name == key:
                # If obj.name != key, it has already been suffixed.
                supers = []
                for sup in obj.super:
                    if isinstance(sup, str):
                        sname = sup
                    else:
                        sname = sup.name
                        if sup.module != obj.module:
                            sname = f'{sup.module}.{sname}'
                    supers.append(sname)
                obj.name += '({})'.format(', '.join(supers))
            obs.append(obj)
    return obs