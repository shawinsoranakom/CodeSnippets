def try_transform(self, lhs, name, lookups=None):
        """
        Helper method for build_lookup(). Try to fetch and initialize
        a transform for name parameter from lhs.
        """
        transform_class = lhs.get_transform(name)
        if transform_class:
            return transform_class(lhs)
        else:
            output_field = lhs.output_field.__class__
            suggested_lookups = difflib.get_close_matches(
                name, lhs.output_field.get_lookups()
            )
            if suggested_lookups:
                suggestion = ", perhaps you meant %s?" % " or ".join(suggested_lookups)
            else:
                suggestion = "."
            if lookups is not None:
                name_index = lookups.index(name)
                unsupported_lookup = LOOKUP_SEP.join(lookups[name_index:])
            else:
                unsupported_lookup = name
            raise FieldError(
                "Unsupported lookup '%s' for %s or join on the field not "
                "permitted%s" % (unsupported_lookup, output_field.__name__, suggestion)
            )