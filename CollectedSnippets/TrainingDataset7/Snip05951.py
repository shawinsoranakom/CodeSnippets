def get_ordering_field_columns(self):
        """
        Return a dictionary of ordering field column numbers and asc/desc.
        """
        # We must cope with more than one column having the same underlying
        # sort field, so we base things on column numbers.
        ordering = self._get_default_ordering()
        ordering_fields = {}
        if ORDER_VAR not in self.params:
            # for ordering specified on ModelAdmin or model Meta, we don't know
            # the right column numbers absolutely, because there might be more
            # than one column associated with that ordering, so we guess.
            for field in ordering:
                if isinstance(field, (Combinable, OrderBy)):
                    if not isinstance(field, OrderBy):
                        field = field.asc()
                    if isinstance(field.expression, F):
                        order_type = "desc" if field.descending else "asc"
                        field = field.expression.name
                    else:
                        continue
                elif field.startswith("-"):
                    field = field.removeprefix("-")
                    order_type = "desc"
                else:
                    order_type = "asc"
                for index, attr in enumerate(self.list_display):
                    if self.get_ordering_field(attr) == field:
                        ordering_fields[index] = order_type
                        break
        else:
            for p in self.params[ORDER_VAR].split("."):
                none, pfx, idx = p.rpartition("-")
                try:
                    idx = int(idx)
                except ValueError:
                    continue  # skip it
                ordering_fields[idx] = "desc" if pfx == "-" else "asc"
        return ordering_fields