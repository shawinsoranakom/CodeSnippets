def _read_group_groupby_properties(self, alias: str, field: Field, property_name: str, query: Query) -> SQL:
        fname = field.name
        definition = self.get_property_definition(f"{fname}.{property_name}")
        property_type = definition.get('type')
        sql_property = self._field_to_sql(alias, f'{fname}.{property_name}', query)

        # JOIN on the JSON array
        if property_type in ('tags', 'many2many'):
            property_alias = query.make_alias(alias, f'{fname}_{property_name}')
            sql_property = SQL(
                """ CASE
                        WHEN jsonb_typeof(%(property)s) = 'array'
                        THEN %(property)s
                        ELSE '[]'::jsonb
                     END """,
                property=sql_property,
            )
            if property_type == 'tags':
                # ignore invalid tags
                tags = [tag[0] for tag in definition.get('tags') or []]
                # `->>0 : convert "JSON string" into string
                condition = SQL(
                    "%s->>0 = ANY(%s::text[])",
                    SQL.identifier(property_alias), tags,
                )
            else:
                comodel = self.env.get(definition.get('comodel'))
                if comodel is None or comodel._transient or comodel._abstract:
                    raise UserError(_(
                        "You cannot use “%(property_name)s” because the linked “%(model_name)s” model doesn't exist or is invalid",
                        property_name=definition.get('string', property_name), model_name=definition.get('comodel'),
                    ))

                # check the existences of the many2many
                condition = SQL(
                    "%s::int IN (SELECT id FROM %s)",
                    SQL.identifier(property_alias), SQL.identifier(comodel._table),
                )

            query.add_join(
                "LEFT JOIN",
                property_alias,
                SQL("jsonb_array_elements(%s)", sql_property),
                condition,
            )

            return SQL.identifier(property_alias)

        elif property_type == 'selection':
            options = [option[0] for option in definition.get('selection') or ()]

            # check the existence of the option
            property_alias = query.make_alias(alias, f'{fname}_{property_name}')
            query.add_join(
                "LEFT JOIN",
                property_alias,
                SQL("(SELECT unnest(%s::text[]) %s)", options, SQL.identifier(property_alias)),
                SQL("%s->>0 = %s", sql_property, SQL.identifier(property_alias)),
            )

            return SQL.identifier(property_alias)

        elif property_type == 'many2one':
            comodel = self.env.get(definition.get('comodel'))
            if comodel is None or comodel._transient or comodel._abstract:
                raise UserError(_(
                    "You cannot use “%(property_name)s” because the linked “%(model_name)s” model doesn't exist or is invalid",
                    property_name=definition.get('string', property_name), model_name=definition.get('comodel'),
                ))

            return SQL(
                """ CASE
                        WHEN jsonb_typeof(%(property)s) = 'number'
                         AND (%(property)s)::int IN (SELECT id FROM %(table)s)
                        THEN %(property)s
                        ELSE NULL
                     END """,
                property=sql_property,
                table=SQL.identifier(comodel._table),
            )

        elif property_type == 'date':
            return SQL(
                """ CASE
                        WHEN jsonb_typeof(%(property)s) = 'string'
                        THEN (%(property)s->>0)::DATE
                        ELSE NULL
                     END """,
                property=sql_property,
            )

        elif property_type == 'datetime':
            return SQL(
                """ CASE
                        WHEN jsonb_typeof(%(property)s) = 'string'
                        THEN to_timestamp(%(property)s->>0, 'YYYY-MM-DD HH24:MI:SS')
                        ELSE NULL
                     END """,
                property=sql_property,
            )

        elif property_type == 'html':
            raise UserError(_('Grouping by HTML properties is not supported.'))

        # if the key is not present in the dict, fallback to false instead of none
        return SQL("COALESCE(%s, 'false')", sql_property)