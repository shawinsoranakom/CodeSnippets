def _search_panel_sanitized_parent_hierarchy(self, records, parent_name, ids):
        """
        Filter the provided list of records to ensure the following properties of
        the resulting sublist:

        1) it is closed for the parent relation
        2) every record in it is an ancestor of a record with id in ids
           (if ``ids = records.ids``, that condition is automatically
           satisfied)
        3) it is maximal among other sublists with properties 1 and 2.

        :param list[dict] records: the list of records to filter, the
            records must have the form::

                { 'id': id, parent_name: False or (id, display_name),... }

        :param str parent_name: indicates which key determines the parent
        :param list[int] ids: list of record ids
        :return: the sublist of records with the above properties
        """
        def get_parent_id(record):
            value = record[parent_name]
            return value and value[0]

        allowed_records = { record['id']: record for record in records }
        records_to_keep = {}
        for id in ids:
            record_id = id
            ancestor_chain = {}
            chain_is_fully_included = True
            while chain_is_fully_included and record_id:
                known_status = records_to_keep.get(record_id)
                if known_status is not None:
                    # the record and its known ancestors have already been considered
                    chain_is_fully_included = known_status
                    break
                record = allowed_records.get(record_id)
                if record:
                    ancestor_chain[record_id] = record
                    record_id = get_parent_id(record)
                else:
                    chain_is_fully_included = False

            for r_id in ancestor_chain:
                records_to_keep[r_id] = chain_is_fully_included

        # we keep initial order
        return [rec for rec in records if records_to_keep.get(rec['id'])]