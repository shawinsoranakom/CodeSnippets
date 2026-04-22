def new_is_type(obj, type_matchers):
        if type(type_matchers) is not tuple:
            type_matchers = (type_matchers,)

        for type_matcher in type_matchers:
            if type_matcher in true_type_matchers:
                return True
        return False