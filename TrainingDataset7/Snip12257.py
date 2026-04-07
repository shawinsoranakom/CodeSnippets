def solve_lookup_type(self, lookup, summarize=False):
        """
        Solve the lookup type from the lookup (e.g.: 'foobar__id__icontains').
        """
        lookup_splitted = lookup.split(LOOKUP_SEP)
        if self.annotations:
            annotation, expression_lookups = refs_expression(
                lookup_splitted, self.annotations
            )
            if annotation:
                expression = self.annotations[annotation]
                if summarize:
                    expression = Ref(annotation, expression)
                return expression_lookups, (), expression
        _, field, _, lookup_parts = self.names_to_path(lookup_splitted, self.get_meta())
        field_parts = lookup_splitted[0 : len(lookup_splitted) - len(lookup_parts)]
        if len(lookup_parts) > 1 and not field_parts:
            raise FieldError(
                'Invalid lookup "%s" for model %s".'
                % (lookup, self.get_meta().model.__name__)
            )
        return lookup_parts, field_parts, False