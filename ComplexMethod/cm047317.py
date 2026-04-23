def _update_xmlids(self, data_list, update=False):
        """ Create or update the given XML ids.

            :param data_list: list of dicts with keys `xml_id` (XMLID to
                assign), `noupdate` (flag on XMLID), `record` (target record).
            :param update: should be ``True`` when upgrading a module
        """
        if not data_list:
            return

        rows = tools.OrderedSet()
        for data in data_list:
            prefix, suffix = data['xml_id'].split('.', 1)
            record = data['record']
            noupdate = bool(data.get('noupdate'))
            rows.add((prefix, suffix, record._name, record.id, noupdate))

        for sub_rows in split_every(self.env.cr.IN_MAX, rows):
            # insert rows or update them
            query = self._build_update_xmlids_query(sub_rows, update)
            try:
                self.env.cr.execute(query, [arg for row in sub_rows for arg in row])
                result = self.env.cr.fetchall()
                if result:
                    for module, name, model, res_id, create_date, write_date in result:
                        # small optimisation: during install a lot of xmlid are created/updated.
                        # Instead of clearing the cache, set the correct value in the cache to avoid a bunch of query
                        self._xmlid_lookup.__cache__.add_value(self, f"{module}.{name}", cache_value=(model, res_id))
                        if create_date != write_date:
                            # something was updated, notify other workers
                            # it is possible that create_date and write_date
                            # have the same value after an update if it was
                            # created in the same transaction, no need to invalidate other worker cache
                            # cache in this case.
                            self.env.registry.cache_invalidated.add('default')

            except Exception:
                _logger.error("Failed to insert ir_model_data\n%s", "\n".join(str(row) for row in sub_rows))
                raise

        # update loaded_xmlids
        self.pool.loaded_xmlids.update("%s.%s" % row[:2] for row in rows)

        if any(row[2] == 'res.groups' for row in rows):
            self.env.registry.clear_cache('groups')