def use_one_line_repr(obj):
                # iterable types
                if type(obj) in (list, tuple, dict):
                    # get all types
                    element_types = []
                    if type(obj) is dict:
                        element_types.extend(type(x) for x in obj.values())
                    elif type(obj) in [list, tuple]:
                        element_types.extend(type(x) for x in obj)

                    # At least one element is of iterable type
                    if any(x in (list, tuple, dict) for x in element_types):
                        # If `obj` has more than one element and at least one of them is iterable --> no one line repr.
                        if len(obj) > 1:
                            return False

                        # only one element that is iterable, but not the same type as `obj` --> no one line repr.
                        if type(obj) is not type(obj[0]):
                            return False

                        # one-line repr. if possible, without width limit
                        return no_new_line_in_elements

                    # all elements are of simple types, but more than one type --> no one line repr.
                    if len(set(element_types)) > 1:
                        return False

                    # all elements are of the same simple type
                    if element_types[0] in [int, float]:
                        # one-line repr. without width limit
                        return no_new_line_in_elements
                    elif element_types[0] is str:
                        if len(obj) == 1:
                            # one single string element --> one-line repr. without width limit
                            return no_new_line_in_elements
                        else:
                            # multiple string elements --> one-line repr. if fit into width limit
                            return could_use_one_line

                # simple types (int, flat, string)
                return True