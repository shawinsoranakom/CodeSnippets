def _search_phone_mobile_search(self, operator, value):
        if operator == 'not in':
            return Domain.AND(self._search_phone_mobile_search('!=', v) for v in value)
        if operator == 'in':
            return Domain.OR(self._search_phone_mobile_search('=', v) for v in value)
        value = value.strip() if isinstance(value, str) else value
        phone_fields = [
            fname for fname in self._phone_get_number_fields()
            if fname in self._fields and self._fields[fname].store
        ]
        if not phone_fields:
            raise UserError(_('Missing definition of phone fields.'))

        # search if phone/mobile is set or not
        if (value is True or not value) and operator in ('=', '!='):
            if value:
                # inverse the operator
                operator = '=' if operator == '!=' else '!='
            op = Domain.AND if operator == '=' else Domain.OR
            return op(Domain(phone_field, operator, False) for phone_field in phone_fields)

        if not value:
            return Domain.TRUE
        if self._phone_search_min_length and len(value) < self._phone_search_min_length:
            raise UserError(_('Please enter at least 3 characters when searching a Phone number.'))

        sql_operator = {'=like': 'LIKE', '=ilike': 'ILIKE'}.get(operator, operator)

        if value.startswith('+') or value.startswith('00'):
            if operator in Domain.NEGATIVE_OPERATORS:
                # searching on +32485112233 should also finds 0032485112233 (and vice versa)
                # we therefore remove it from input value and search for both of them in db
                where_str = ' AND '.join(
                    f"""model.{phone_field} IS NULL OR (
                            REGEXP_REPLACE(model.{phone_field}, %s, '', 'g') {sql_operator} %s OR
                            REGEXP_REPLACE(model.{phone_field}, %s, '', 'g') {sql_operator} %s
                    )"""
                    for phone_field in phone_fields
                )
            else:
                # searching on +32485112233 should also finds 0032485112233 (and vice versa)
                # we therefore remove it from input value and search for both of them in db
                where_str = ' OR '.join(
                    f"""model.{phone_field} IS NOT NULL AND (
                            REGEXP_REPLACE(model.{phone_field}, %s, '', 'g') {sql_operator} %s OR
                            REGEXP_REPLACE(model.{phone_field}, %s, '', 'g') {sql_operator} %s
                    )"""
                    for phone_field in phone_fields
                )
            query = f"SELECT model.id FROM {self._table} model WHERE {where_str};"

            term = re.sub(PHONE_REGEX_PATTERN, '', value[1 if value.startswith('+') else 2:])
            if operator not in ('=', '!='):  # for like operators
                term = f'{term}%'
            self.env.cr.execute(
                query, (PHONE_REGEX_PATTERN, '00' + term, PHONE_REGEX_PATTERN, '+' + term) * len(phone_fields)
            )
        else:
            if operator in Domain.NEGATIVE_OPERATORS:
                where_str = ' AND '.join(
                    f"(model.{phone_field} IS NULL OR REGEXP_REPLACE(model.{phone_field}, %s, '', 'g') {sql_operator} %s)"
                    for phone_field in phone_fields
                )
            else:
                where_str = ' OR '.join(
                    f"(model.{phone_field} IS NOT NULL AND REGEXP_REPLACE(model.{phone_field}, %s, '', 'g') {sql_operator} %s)"
                    for phone_field in phone_fields
                )
            query = f"SELECT model.id FROM {self._table} model WHERE {where_str};"
            term = re.sub(PHONE_REGEX_PATTERN, '', value)
            if operator not in ('=', '!='):  # for like operators
                term = f'%{term}%'
            self.env.cr.execute(query, (PHONE_REGEX_PATTERN, term) * len(phone_fields))
        res = self.env.cr.fetchall()
        return Domain('id', 'in', [r[0] for r in res])