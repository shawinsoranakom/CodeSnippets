def convert_table(self, table, fields, pwd, with_commit=False, unobfuscate=False):
        cypherings = []
        cyph_fct = self.uncypher_string if unobfuscate else self.cypher_string

        for field in fields:
            field_type = self.check_field(table, field)
            sql_field = SQL.identifier(field)
            if field_type == 'string':
                cypher_query = cyph_fct(sql_field, pwd)
                cypherings.append(SQL('%s=%s', SQL.identifier(field), cypher_query))
            elif field_type == 'json':
                # List every key
                # Loop on keys
                # Nest the jsonb_set calls to update all values at once
                # Do not create the key in json if doesn't esist
                new_field_value = sql_field
                self.cr.execute(SQL('select distinct jsonb_object_keys(%s) as key from %s', sql_field, SQL.identifier(table)))
                keys = [k[0] for k in self.cr.fetchall()]
                for key in keys:
                    cypher_query = cyph_fct(SQL("%s->>%s", sql_field, key), pwd)
                    new_field_value = SQL(
                        """jsonb_set(%s, array[%s], to_jsonb(%s)::jsonb, FALSE)""",
                        new_field_value, key, cypher_query
                    )
                cypherings.append(SQL('%s=%s', sql_field, new_field_value))

        if cypherings:
            query = SQL("UPDATE %s SET %s", SQL.identifier(table), SQL(',').join(cypherings))
            self.cr.execute(query)
            if with_commit:
                self.commit()
                self.begin()