def cleanse_special_types(self, request, value):
        try:
            # If value is lazy or a complex object of another kind, this check
            # might raise an exception. isinstance checks that lazy
            # MultiValueDicts will have a return value.
            is_multivalue_dict = isinstance(value, MultiValueDict)
        except Exception as e:
            return "{!r} while evaluating {!r}".format(e, value)

        if is_multivalue_dict:
            # Cleanse MultiValueDicts (request.POST is the one we usually care
            # about)
            value = self.get_cleansed_multivaluedict(request, value)
        return value