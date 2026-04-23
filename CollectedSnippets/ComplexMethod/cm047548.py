def _extract_records(self, field_paths, data, log=lambda a: None, limit=float('inf')):
        """ Generates record dicts from the data sequence.

        The result is a generator of dicts mapping field names to raw
        (unconverted, unvalidated) values.

        For relational fields, if sub-fields were provided the value will be
        a list of sub-records

        The following sub-fields may be set on the record (by key):

        * None is the display_name for the record (to use with name_create/name_search)
        * "id" is the External ID for the record
        * ".id" is the Database ID for the record
        """
        fields = self._fields

        get_o2m_values = itemgetter_tuple([
            index
            for index, fnames in enumerate(field_paths)
            if fnames[0] in fields and fields[fnames[0]].type == 'one2many'
        ])
        get_nono2m_values = itemgetter_tuple([
            index
            for index, fnames in enumerate(field_paths)
            if fnames[0] not in fields or fields[fnames[0]].type != 'one2many'
        ])
        # Checks if the provided row has any non-empty one2many fields
        def only_o2m_values(row):
            return any(get_o2m_values(row)) and not any(get_nono2m_values(row))

        property_definitions = {}
        property_columns = defaultdict(list)
        for fname, *__ in field_paths:
            if not fname:
                continue
            if '.' not in fname:
                if fname not in fields:
                    raise ValueError(f'Invalid field name {fname!r}')
                continue

            f_prop_name, property_name = fname.split('.')
            if f_prop_name not in fields or fields[f_prop_name].type != 'properties':
                # Can be .id
                continue

            definition = self.get_property_definition(fname)
            if not definition:
                # Can happen if someone remove the property, UserError ?
                raise ValueError(f"Property {property_name!r} doesn't have any definition on {fname!r} field")

            property_definitions[fname] = definition
            property_columns[f_prop_name].append(fname)

        # m2o fields can't be on multiple lines so don't take it in account
        # for only_o2m_values rows filter, but special-case it later on to
        # be handled with relational fields (as it can have subfields).
        def is_relational(fname):
            return (
                fname in fields and
                fields[fname].relational
            ) or (
                fname in property_definitions and
                property_definitions[fname].get('type') in ('many2one', 'many2many')
            )

        index = 0
        while index < len(data) and index < limit:
            row = data[index]

            # copy non-relational fields to record dict
            record = {
                fnames[0]: value
                for fnames, value in zip(field_paths, row)
                if not is_relational(fnames[0])
            }

            # Get all following rows which have relational values attached to
            # the current record (no non-relational values)
            record_span = itertools.takewhile(
                only_o2m_values,
                (data[j] for j in range(index + 1, len(data))),
            )
            # stitch record row back on for relational fields
            record_span = list(itertools.chain([row], record_span))

            for relfield, *__ in field_paths:
                if not is_relational(relfield):
                    continue

                if relfield not in property_definitions:
                    comodel = self.env[fields[relfield].comodel_name]
                else:
                    comodel = self.env[property_definitions[relfield]['comodel']]

                # get only cells for this sub-field, should be strictly
                # non-empty, field path [None] is for display_name field
                indices, subfields = zip(*((index, fnames[1:] or [None])
                                           for index, fnames in enumerate(field_paths)
                                           if fnames[0] == relfield))

                # return all rows which have at least one value for the
                # subfields of relfield
                relfield_data = [it for it in map(itemgetter_tuple(indices), record_span) if any(it)]
                record[relfield] = [
                    subrecord
                    for subrecord, _subinfo in comodel._extract_records(subfields, relfield_data, log=log)
                ]

            for properties_fname, property_indexes_names in property_columns.items():
                properties = []
                for property_name in property_indexes_names:
                    value = record.pop(property_name)
                    properties.append(dict(**property_definitions[property_name], value=value))
                record[properties_fname] = properties

            yield record, {'rows': {
                'from': index,
                'to': index + len(record_span) - 1,
            }}
            index += len(record_span)