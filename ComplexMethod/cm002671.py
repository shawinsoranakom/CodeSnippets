def _is_valid_text_input(t):
            if isinstance(t, str):
                return True
            elif isinstance(t, (list, tuple)):
                if len(t) == 0:
                    return True
                elif isinstance(t[0], str):
                    return True
                elif isinstance(t[0], (list, tuple)):
                    if len(t[0]) == 0 or isinstance(t[0][0], str):
                        return True
                    elif isinstance(t[0][0], (list, tuple)):
                        return len(t[0][0]) == 0 or isinstance(t[0][0][0], str)
                    else:
                        return False
                else:
                    return False
            else:
                return False