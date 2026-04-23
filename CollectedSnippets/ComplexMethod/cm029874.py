def _compare(a, b):
        # Compare two fields on an AST object, which may themselves be
        # AST objects, lists of AST objects, or primitive ASDL types
        # like identifiers and constants.
        if isinstance(a, AST):
            return compare(
                a,
                b,
                compare_attributes=compare_attributes,
            )
        elif isinstance(a, list):
            # If a field is repeated, then both objects will represent
            # the value as a list.
            if len(a) != len(b):
                return False
            for a_item, b_item in zip(a, b):
                if not _compare(a_item, b_item):
                    return False
            else:
                return True
        else:
            return type(a) is type(b) and a == b