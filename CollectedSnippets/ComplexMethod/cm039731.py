def _decode(self, s, encode_nominal=False, matrix_type=DENSE):
        '''Do the job the ``encode``.'''

        # Make sure this method is idempotent
        self._current_line = 0

        # If string, convert to a list of lines
        if isinstance(s, str):
            s = s.strip('\r\n ').replace('\r\n', '\n').split('\n')

        # Create the return object
        obj: ArffContainerType = {
            'description': '',
            'relation': '',
            'attributes': [],
            'data': []
        }
        attribute_names = {}

        # Create the data helper object
        data = _get_data_object_for_decoding(matrix_type)

        # Read all lines
        STATE = _TK_DESCRIPTION
        s = iter(s)
        for row in s:
            self._current_line += 1
            # Ignore empty lines
            row = row.strip(' \r\n')
            if not row: continue

            u_row = row.upper()

            # DESCRIPTION -----------------------------------------------------
            if u_row.startswith(_TK_DESCRIPTION) and STATE == _TK_DESCRIPTION:
                obj['description'] += self._decode_comment(row) + '\n'
            # -----------------------------------------------------------------

            # RELATION --------------------------------------------------------
            elif u_row.startswith(_TK_RELATION):
                if STATE != _TK_DESCRIPTION:
                    raise BadLayout()

                STATE = _TK_RELATION
                obj['relation'] = self._decode_relation(row)
            # -----------------------------------------------------------------

            # ATTRIBUTE -------------------------------------------------------
            elif u_row.startswith(_TK_ATTRIBUTE):
                if STATE != _TK_RELATION and STATE != _TK_ATTRIBUTE:
                    raise BadLayout()

                STATE = _TK_ATTRIBUTE

                attr = self._decode_attribute(row)
                if attr[0] in attribute_names:
                    raise BadAttributeName(attr[0], attribute_names[attr[0]])
                else:
                    attribute_names[attr[0]] = self._current_line
                obj['attributes'].append(attr)

                if isinstance(attr[1], (list, tuple)):
                    if encode_nominal:
                        conversor = EncodedNominalConversor(attr[1])
                    else:
                        conversor = NominalConversor(attr[1])
                else:
                    CONVERSOR_MAP = {'STRING': str,
                                     'INTEGER': lambda x: int(float(x)),
                                     'NUMERIC': float,
                                     'REAL': float}
                    conversor = CONVERSOR_MAP[attr[1]]

                self._conversors.append(conversor)
            # -----------------------------------------------------------------

            # DATA ------------------------------------------------------------
            elif u_row.startswith(_TK_DATA):
                if STATE != _TK_ATTRIBUTE:
                    raise BadLayout()

                break
            # -----------------------------------------------------------------

            # COMMENT ---------------------------------------------------------
            elif u_row.startswith(_TK_COMMENT):
                pass
            # -----------------------------------------------------------------
        else:
            # Never found @DATA
            raise BadLayout()

        def stream():
            for row in s:
                self._current_line += 1
                row = row.strip()
                # Ignore empty lines and comment lines.
                if row and not row.startswith(_TK_COMMENT):
                    yield row

        # Alter the data object
        obj['data'] = data.decode_rows(stream(), self._conversors)
        if obj['description'].endswith('\n'):
            obj['description'] = obj['description'][:-1]

        return obj