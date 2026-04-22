def set_tos(t):
        nonlocal tos
        if tos is not None:
            # Hash tos so we support reading multiple objects
            refs.append(tos)
        tos = t