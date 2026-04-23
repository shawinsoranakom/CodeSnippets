def assertRecordValues(
            self,
            records: odoo.models.BaseModel,
            expected_values: list[dict],
            *,
            field_names: Optional[Iterable[str]] = None,
    ) -> None:
        ''' Compare a recordset with a list of dictionaries representing the expected results.
        This method performs a comparison element by element based on their index.
        Then, the order of the expected values is extremely important.

        .. note::

            - ``None`` expected values can be used for empty fields.
            - x2many fields are expected by ids (so the expected value should be
              a ``list[int]``
            - many2one fields are expected by id (so the expected value should
              be an ``int``

        :param records: The records to compare.
        :param expected_values: Items to check the ``records`` against.
        :param field_names: list of fields to check during comparison, if
                            unspecified all expected_values must have the same
                            keys and all are checked
        '''
        if not field_names:
            field_names = expected_values[0].keys()
            for i, v in enumerate(expected_values):
                self.assertEqual(
                    v.keys(), field_names,
                    f"All expected values must have the same keys, found differences between records 0 and {i}",
                )

        expected_reformatted = []
        for vs in expected_values:
            r = {}
            for f in field_names:
                t = records._fields[f].type
                if t in ('one2many', 'many2many'):
                    r[f] = sorted(vs[f])
                elif t == 'float':
                    r[f] = float(vs[f])
                elif t == 'integer':
                    r[f] = int(vs[f])
                elif vs[f] is None:
                    r[f] = False
                else:
                    r[f] = vs[f]
            expected_reformatted.append(r)

        record_reformatted = []
        for record in records:
            r = {}
            for field_name in field_names:
                record_value = record[field_name]
                match record._fields[field_name]:
                    case odoo.fields.Many2one():
                        record_value = record_value.id
                    case odoo.fields.One2many() | odoo.fields.Many2many():
                        record_value = sorted(record_value.ids)
                    case odoo.fields.Float() as field if digits := field.get_digits(record.env):
                        record_value = Approx(record_value, digits[1], decorate=False)
                    case odoo.fields.Monetary() as field if currency_field_name := field.get_currency_field(record):
                        # don't round if there's no currency set
                        if c := record[currency_field_name]:
                            record_value = Approx(record_value, c, decorate=False)

                r[field_name] = record_value
            record_reformatted.append(r)

        try:
            self.assertSequenceEqual(expected_reformatted, record_reformatted, seq_type=list)
            return
        except AssertionError as e:
            standardMsg, _, diffMsg = str(e).rpartition('\n')
            if 'self.maxDiff' not in diffMsg:
                raise
            # move out of handler to avoid exception chaining

        diffMsg = "".join(difflib.unified_diff(
            pprint.pformat(expected_reformatted).splitlines(keepends=True),
            pprint.pformat(record_reformatted).splitlines(keepends=True),
            fromfile="expected", tofile="records",
        ))
        self.fail(self._formatMessage(None, standardMsg + '\n' + diffMsg))