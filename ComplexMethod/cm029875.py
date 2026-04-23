def _compare_fields(a, b):
        if a._fields != b._fields:
            return False
        for field in a._fields:
            a_field = getattr(a, field, sentinel)
            b_field = getattr(b, field, sentinel)
            if a_field is sentinel and b_field is sentinel:
                # both nodes are missing a field at runtime
                continue
            if a_field is sentinel or b_field is sentinel:
                # one of the node is missing a field
                return False
            if not _compare(a_field, b_field):
                return False
        else:
            return True