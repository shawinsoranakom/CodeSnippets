def _basic_enumerate_words(self, search_details, search, limit):
        """
        Browses through all words that need to be compared to the search term.
        It extracts all words of every field associated to models in the fields_per_model parameter.

        :param search_details: obtained from `_search_get_details()`
        :param search: search term to which words must be matched against
        :param limit: maximum number of records fetched per model to build the word list
        :return: yields words
        """
        match_pattern = r'[\w./-]{%s,}' % min(4, len(search) - 3)
        first = escape_psql(search[0])
        for search_detail in search_details:
            model_name, fields = search_detail['model'], search_detail['search_fields']
            model = self.env[model_name]
            if search_detail.get('requires_sudo'):
                model = model.sudo()
            domain = Domain.AND(search_detail['base_domain'])
            direct_fields = set(fields).intersection(model._fields)
            indirect_fields = self._search_get_indirect_fields(fields, model)
            fields = direct_fields.union(indirect_fields)
            fields_domain = Domain.OR(
                Domain(field, '=ilike', pattern)
                for field in fields
                for pattern in (
                    '%s%%' % first,
                    '%% %s%%' % first,
                    '%%>%s%%' % first,  # HTML
                )
            )
            domain &= fields_domain
            perf_limit = 1000
            records = model.search_read(domain, direct_fields, limit=perf_limit)
            if len(records) == perf_limit:
                # Exact match might have been missed because the fetched
                # results are limited for performance reasons.
                exact_records, _ = model._search_fetch(search_detail, search, 1, None)
                if exact_records:
                    yield search
            for record in records:
                for field, value in record.items():
                    if isinstance(value, str):
                        value = value.lower()
                        if field == 'arch_db':
                            value = text_from_html(value)
                        for word in re.findall(match_pattern, value):
                            if word[0] == search[0]:
                                yield word.lower()
            if indirect_fields:
                records = model.search(domain, limit=limit)
                for indirect_field in indirect_fields:
                    for value in records.mapped(indirect_field):
                        if isinstance(value, str):
                            value = value.lower()
                            yield from re.findall(match_pattern, value)