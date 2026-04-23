def _merge_data(self, fnames=None):
        """ Prepare lead/opp data into a dictionary for merging. Different types
            of fields are processed in different ways:
                - text: all the values are concatenated
                - m2m and o2m: those fields aren't processed
                - m2o: the first not null value prevails (the other are dropped)
                - any other type of field: same as m2o

            :param fnames: list of fields to process
            :returns: contains the merged values of the new opportunity
            :rtype: dict
        """
        if fnames is None:
            fnames = self._merge_get_fields()
        fcallables = self._merge_get_fields_specific()
        address_values = self._merge_get_fields_address()

        # helpers
        def _get_first_not_null(attr, opportunities):
            value = False
            for opp in opportunities:
                if opp[attr]:
                    value = opp[attr].id if isinstance(opp[attr], models.BaseModel) else opp[attr]
                    break
            return value

        # process the field's values
        data = {}
        for field_name in fnames:
            field = self._fields.get(field_name)
            if field is None:
                continue

            fcallable = fcallables.get(field_name)
            if fcallable and callable(fcallable):
                data[field_name] = fcallable(field_name, self)
            elif field_name in address_values:
                data[field_name] = address_values[field_name]
            elif not fcallable and field.type in ('many2many', 'one2many'):
                continue
            else:
                data[field_name] = _get_first_not_null(field_name, self)  # take the first not null

        return data