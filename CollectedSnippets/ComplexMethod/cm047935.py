def _get_mapping_suggestion(self, header, fields_tree, header_types, mapping_fields):
        """ Attempts to match a given header to a field of the imported model.

            We can distinguish 2 types of header format:

            - simple header string that aim to directly match a field of the target model
              e.g.: "lead_id" or "Opportunities" or "description".
            - composed '/' joined header string that aim to match a field of a
              relation field of the target model (= subfield) e.g.:
              'lead_id/description' aim to match the field ``description`` of the field lead_id.

            When returning result, to ease further treatments, the result is
            returned as a list, where each element of the list is a field or
            a sub-field of the preceding field.

            - ``["lead_id"]`` for simple case = simple matching
            - ``["lead_id", "description"]`` for composed case = hierarchy matching

            Mapping suggestion is found using the following heuristic:

            - first we check if there was a saved mapping by the user
            - then try to make an exact match on the field technical name /
              english label / translated label
            - finally, try the "fuzzy match": word distance between the header
              title and the field technical name / english label / translated
              label, using the lowest result. The field used for the fuzzy match
              are based on the field types we extracted from the header data
              (see :meth:`_extract_header_types`).

            For subfields, use the same logic.

            Word distance is a score between 0 and 1 to express the distance
            between two char strings where ``0`` denotes an exact match and
            ``1`` indicates completely different strings

            In order to keep only one column matched per field, we return the
            distance. That distance will be used during the deduplicate process
            (see :meth:`_deduplicate_mapping_suggestions`) and only the
            mapping with the smallest distance will be kept in case of multiple
            mapping on the same field. Note that we don't need to return the
            distance in case of hierachy mapping as we consider that as an
            advanced behaviour. The deduplicate process will ignore hierarchy
            mapping. The user will have to manually select on which field he
            wants to map what in case of mapping duplicates for sub-fields.

            :param str header: header name from the file
            :param list fields_tree: list of all the field of the target model
                Coming from :meth:`get_fields_tree`
                e.g: ``[ { 'name': 'fieldName', 'string': 'fieldLabel', fields: [ { 'name': 'subfieldName', ...} ]} , ... ]``
            :param list header_types: Extracted field types for each column in the parsed file, based on its data content.
                Coming from :meth:`_extract_header_types`
                e.g.: ``['int', 'float', 'char', 'many2one', ...]``
            :param dict mapping_fields: contains the previously saved mapping between header and field for the current model.
                E.g.: ``{ header_name: field_name }``
            :returns: if the header couldn't be matched: an empty dict
                      else: a dict with the field path and the distance between header and the matched field.
            :rtype: ``dict(field_path + Word distance)``

                    In case of simple matching: ``{'field_path': [field_name], distance: word_distance}``
                                           e.g.: ``{'field_path': ['lead_id'], distance: 0.23254}``
                    In case of hierarchy matching: ``{'field_path': [parent_field_name, child_field_name, subchild_field_name]}``
                                              e.g.: ``{'field_path': ['lead_id', 'description']}``
        """
        if not fields_tree:
            return {}

        # First, check in saved mapped fields
        mapping_field_name = mapping_fields.get(header.lower())
        if mapping_field_name and mapping_field_name:
            return {
                'field_path': [name for name in mapping_field_name.split('/')],
                'distance': -1  # Trick to force to keep that match during mapping deduplication.
            }

        if '/' not in header:
            IrModelFieldsUs = self.with_context(lang='en_US').env['ir.model.fields']
            for field in fields_tree:
                fname = field['name']
                # exact match found based on the field technical name
                if header.casefold() == fname.casefold():
                    break
                # match found using either user translation, either model defined field label
                if header.casefold() == field['string'].casefold():
                    break
                field_strings_en = IrModelFieldsUs.get_field_string(field['model_name'])
                if fname in field_strings_en and header.casefold() == field_strings_en[fname].casefold():
                    break
            else:
                field = None

            if field:  # found an exact match, no need to go further
                return {
                    'field_path': [field['name']],
                    'distance': 0
                }

            # If no match found, try fuzzy match on fields filtered based on extracted header types
            # Filter out fields with types that does not match corresponding header types.
            filtered_fields = self._filter_fields_by_types(fields_tree, header_types)
            if not filtered_fields:
                return {}

            min_dist = 1
            min_dist_field = False
            for field in filtered_fields:
                fname = field['name']
                # use string distance for fuzzy match only on most likely field types
                distances = [
                    self._get_distance(header.casefold(), fname.casefold()),
                    self._get_distance(header.casefold(), field['string'].casefold()),
                ]

                if field_string_en := IrModelFieldsUs.get_field_string(field['model_name']).get(fname):
                    distances.append(
                        self._get_distance(header.casefold(), field_string_en.casefold()),
                    )

                # Keep only the closest mapping suggestion. Note that in case of multiple mapping on the same field,
                # a mapping suggestion could be canceled by another one that has a smaller distance on the same field.
                # See 'deduplicate_mapping_suggestions' method for more info.
                current_field_dist = min(distances)
                if current_field_dist < min_dist:
                    min_dist_field = fname
                    min_dist = current_field_dist

            if min_dist < self.FUZZY_MATCH_DISTANCE:
                return {
                    'field_path': [min_dist_field],
                    'distance': min_dist
                }

            return {}

        # relational field path
        field_path = []
        subfields_tree = fields_tree
        # Iteratively dive into fields tree
        for sub_header in header.split('/'):
            # Strip sub_header in case spaces are added around '/' for
            # readability of paths
            # Skip Saved mapping (mapping_field = {})
            match = self._get_mapping_suggestion(sub_header.strip(), subfields_tree, header_types, {})
            # Any match failure, exit
            if not match:
                return {}
            # prep subfields for next iteration within match['name'][0]
            field_name = match['field_path'][0]
            subfields_tree = next(item['fields'] for item in subfields_tree if item['name'] == field_name)
            field_path.append(field_name)
        # No need to return distance for hierarchy mapping
        return {'field_path': field_path}