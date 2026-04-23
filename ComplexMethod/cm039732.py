def iter_encode(self, obj):
        '''The iterative version of `arff.ArffEncoder.encode`.

        This encodes iteratively a given object and return, one-by-one, the
        lines of the ARFF file.

        :param obj: the object containing the ARFF information.
        :return: (yields) the ARFF file as strings.
        '''
        # DESCRIPTION
        if obj.get('description', None):
            for row in obj['description'].split('\n'):
                yield self._encode_comment(row)

        # RELATION
        if not obj.get('relation'):
            raise BadObject('Relation name not found or with invalid value.')

        yield self._encode_relation(obj['relation'])
        yield ''

        # ATTRIBUTES
        if not obj.get('attributes'):
            raise BadObject('Attributes not found.')

        attribute_names = set()
        for attr in obj['attributes']:
            # Verify for bad object format
            if not isinstance(attr, (tuple, list)) or \
               len(attr) != 2 or \
               not isinstance(attr[0], str):
                raise BadObject('Invalid attribute declaration "%s"'%str(attr))

            if isinstance(attr[1], str):
                # Verify for invalid types
                if attr[1] not in _SIMPLE_TYPES:
                    raise BadObject('Invalid attribute type "%s"'%str(attr))

            # Verify for bad object format
            elif not isinstance(attr[1], (tuple, list)):
                raise BadObject('Invalid attribute type "%s"'%str(attr))

            # Verify attribute name is not used twice
            if attr[0] in attribute_names:
                raise BadObject('Trying to use attribute name "%s" for the '
                                'second time.' % str(attr[0]))
            else:
                attribute_names.add(attr[0])

            yield self._encode_attribute(attr[0], attr[1])
        yield ''
        attributes = obj['attributes']

        # DATA
        yield _TK_DATA
        if 'data' in obj:
            data = _get_data_object_for_encoding(obj.get('data'))
            yield from data.encode_data(obj.get('data'), attributes)

        yield ''