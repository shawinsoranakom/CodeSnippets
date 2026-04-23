def _action_unmerge(self):
        """ Unmerge `self` into one account per company in `self.company_ids`.
        This will modify:
            - the many2many and company-dependent fields on `self`
            - the records with relational fields pointing to `self`
        """

        def _get_query_company_id(model):
            """ Get a query giving the `company_id` of a model.

                Uses _field_to_sql, so works even in some cases where `company_id`
                isn't stored, e.g. if it is a related field.

                Returns None if we cannot identify the company_id that corresponds to
                each record, (e.g. if there is no company_id field, or company_id
                is computed non-stored and _field_to_sql isn't implemented for it).
            """
            if model == 'res.company':
                company_id_field = 'id'
            elif 'company_id' in self.env[model]:
                company_id_field = 'company_id'
            else:
                return
            # We would get a ValueError if the _field_to_sql is not implemented. In that case, we return None.
            with contextlib.suppress(ValueError):
                query = Query(self.env, self.env[model]._table, self.env[model]._table_sql)
                return query.select(
                    SQL('%s AS id', self.env[model]._field_to_sql(query.table, 'id')),
                    SQL('%s AS company_id', self.env[model]._field_to_sql(query.table, company_id_field, query)),
                )

        # Step 1: Check access rights.
        self._check_action_unmerge_possible()

        # Step 2: Create new accounts.
        base_company = self.env.company if self.env.company in self.company_ids else self.company_ids[0]
        companies_to_update = self.company_ids - base_company
        check_company_fields = {fname for fname, field in self._fields.items() if field.relational and field.check_company}
        new_account_by_company = {
            company: self.copy(default={
                'name': self.name,
                'company_ids': [Command.set(company.ids)],
                **{
                    fname: self[fname].filtered(lambda record: record.company_id == company)
                    for fname in check_company_fields
                }
            })
            for company in companies_to_update
        }
        new_accounts = self.env['account.account'].union(*new_account_by_company.values())

        # Step 3: Update foreign keys in DB.

        # Invalidate cache
        self.env.invalidate_all()

        new_account_id_by_company_id = {str(company.id): new_account.id for company, new_account in new_account_by_company.items()}
        new_account_id_by_company_id_json = json.dumps(new_account_id_by_company_id)
        (self | new_accounts).invalidate_recordset()

        # 3.1: Update fields on other models that reference account.account
        many2x_fields = self.env['ir.model.fields'].search([
            ('ttype', 'in', ('many2one', 'many2many')),
            ('relation', '=', 'account.account'),
            ('store', '=', True),
            ('company_dependent', '=', False),
        ])
        for field_to_update in many2x_fields:
            model = field_to_update.model
            if not self.env[model]._auto:
                continue
            if not (query_company_id := _get_query_company_id(model)):
                continue
            if field_to_update.ttype == 'many2one':
                table = self.env[model]._table
                account_column = field_to_update.name
                model_column = 'id'
            else:
                table = field_to_update.relation_table
                account_column = field_to_update.column2
                model_column = field_to_update.column1
            self.env.cr.execute(SQL(
                """
                 UPDATE %(table)s
                    SET %(account_column)s = (
                            %(new_account_id_by_company_id_json)s::jsonb->>
                            table_with_company_id.company_id::text
                        )::int
                   FROM (%(query_company_id)s) table_with_company_id
                  WHERE table_with_company_id.id = %(model_column)s
                    AND %(table)s.%(account_column)s = %(account_id)s
                    AND table_with_company_id.company_id IN %(company_ids_to_update)s
                """,
                table=SQL.identifier(table),
                account_column=SQL.identifier(account_column),
                new_account_id_by_company_id_json=new_account_id_by_company_id_json,
                query_company_id=query_company_id,
                model_column=SQL.identifier(table, model_column),
                account_id=self.id,
                company_ids_to_update=tuple(new_account_id_by_company_id),
            ))
        for field in self.env.registry.many2one_company_dependents[self._name]:
            self.env.cr.execute(SQL(
                """
                UPDATE %(table)s
                SET %(column)s = (
                    SELECT jsonb_object_agg(key,
                        CASE
                            WHEN value::int = %(account_id)s AND %(new_account_id_by_company_id_json)s ? key
                            THEN (%(new_account_id_by_company_id_json)s::jsonb->>key)::int
                            ELSE value::int
                        END
                    )
                    FROM jsonb_each_text(%(column)s)
                )
                WHERE %(column)s IS NOT NULL
                """,
                table=SQL.identifier(self.env[field.model_name]._table),
                column=SQL.identifier(field.name),
                new_account_id_by_company_id_json=new_account_id_by_company_id_json,
                account_id=self.id,
            ))

        # 3.2: Update Reference fields that reference account.account
        reference_fields = self.env['ir.model.fields'].search([('ttype', '=', 'reference'), ('store', '=', True)])
        for field_to_update in reference_fields:
            model = field_to_update.model
            if not self.env[model]._auto:
                continue
            if not (query_company_id := _get_query_company_id(model)):
                continue
            self.env.cr.execute(SQL(
                """
                 UPDATE %(table)s
                    SET %(column)s = 'account.account,' || (%(new_account_id_by_company_id_json)s::jsonb->>table_with_company_id.company_id::text)
                   FROM (%(query_company_id)s) table_with_company_id
                  WHERE table_with_company_id.id = %(table)s.id
                    AND %(column)s = %(value_to_update)s
                    AND table_with_company_id.company_id IN %(company_ids_to_update)s
                """,
                table=SQL.identifier(self.env[model]._table),
                column=SQL.identifier(field_to_update.name),
                new_account_id_by_company_id_json=new_account_id_by_company_id_json,
                query_company_id=query_company_id,
                value_to_update=f'account.account,{self.id}',
                company_ids_to_update=tuple(new_account_id_by_company_id),
            ))

        # 3.3: Update Many2OneReference fields that reference account.account
        many2one_reference_fields = self.env['ir.model.fields'].search([
            ('ttype', '=', 'many2one_reference'),
            ('store', '=', True),
            '!', '&', ('model', '=', 'studio.approval.request'),  # A weird Many2oneReference which doesn't have its model field on the model.
                      ('name', '=', 'res_id'),
        ])
        for field_to_update in many2one_reference_fields:
            model = field_to_update.model
            model_field = self.env[model]._fields[field_to_update.name]._related_model_field
            if not self.env[model]._auto or not self.env[model]._fields[model_field].store:
                continue
            if not (query_company_id := _get_query_company_id(model)):
                continue
            self.env.cr.execute(SQL(
                """
                 UPDATE %(table)s
                    SET %(column)s = (%(new_account_id_by_company_id_json)s::jsonb->>table_with_company_id.company_id::text)::int
                   FROM (%(query_company_id)s) table_with_company_id
                  WHERE table_with_company_id.id = %(table)s.id
                    AND %(column)s = %(account_id)s
                    AND %(model_column)s = 'account.account'
                    AND table_with_company_id.company_id IN %(company_ids_to_update)s
                """,
                table=SQL.identifier(self.env[model]._table),
                column=SQL.identifier(field_to_update.name),
                new_account_id_by_company_id_json=new_account_id_by_company_id_json,
                query_company_id=query_company_id,
                account_id=self.id,
                model_column=SQL.identifier(model_field),
                company_ids_to_update=tuple(new_account_id_by_company_id),
            ))

        # 3.4: Update company_dependent fields
        # Dispatch the values of the existing account to the new accounts.
        self.env.cr.execute(SQL(
            """
            WITH new_account_company AS (
                SELECT key AS company_id, value::int AS account_id
                FROM json_each_text(%(new_account_id_by_company_id_json)s)
            )
            UPDATE %(table)s new
            SET %(migrate_fields)s
            FROM %(table)s old, new_account_company a2c
            WHERE old.id = %(old_id)s
            AND a2c.account_id = new.id
            AND new.id IN %(new_ids)s
            """,
            new_account_id_by_company_id_json=new_account_id_by_company_id_json,
            table=SQL.identifier(self._table),
            migrate_fields=SQL(', ').join(
                SQL(
                    """
                    %(field)s = CASE WHEN old.%(field)s ? a2c.company_id
                                THEN jsonb_build_object(a2c.company_id, old.%(field)s->a2c.company_id)
                                ELSE NULL END
                    """,
                    field=SQL.identifier(field_name),
                )
                for field_name, field in self._fields.items()
                if field.company_dependent
            ),
            old_id=self.id,
            new_ids=tuple(new_accounts.ids)
        ))
        # On the original account, remove values for other companies
        self.env.cr.execute(SQL(
            "UPDATE %(table)s SET %(fields_drop_company_ids)s WHERE id = %(id)s",
            table=SQL.identifier(self._table),
            fields_drop_company_ids=SQL(', ').join(
                SQL(
                    "%(field)s = NULLIF(%(field)s - %(company_ids)s, '{}'::jsonb)",
                    field=SQL.identifier(field_name),
                    company_ids=list(new_account_id_by_company_id)
                )
                for field_name, field in self._fields.items()
                if field.company_dependent
            ),
            id=self.id
        ))

        # 3.5. Split account xmlids based on the company_id that is present within the xmlid
        self.env['ir.model.data'].invalidate_model()
        account_id_by_company_id_json = json.dumps({**new_account_id_by_company_id, str(base_company.id): self.id})
        self.env.cr.execute(SQL(
            """
             UPDATE ir_model_data
                SET res_id = (
                        %(account_id_by_company_id_json)s::jsonb->>
                        substring(name, %(xmlid_regex)s)
                    )::int
              WHERE module = 'account'
                AND model = 'account.account'
                AND res_id = %(account_id)s
                AND name ~ %(xmlid_regex)s
            """,
            account_id_by_company_id_json=account_id_by_company_id_json,
            xmlid_regex=r'([\d]+)_.*',
            account_id=self.id,
        ))

        # Clear ir.model.data ormcache
        self.env.registry.clear_cache()

        # Step 4: Change check_company fields to only keep values compatible with the account's company, and update company_ids on account.
        write_vals = {'company_ids': [Command.set(base_company.ids)]}
        check_company_fields = {field for field in self._fields.values() if field.relational and field.check_company}
        for field in check_company_fields:
            corecord = self[field.name]
            filtered_corecord = corecord.filtered_domain(corecord._check_company_domain(base_company))
            write_vals[field.name] = filtered_corecord.id if field.type == 'many2one' else [Command.set(filtered_corecord.ids)]

        self.write(write_vals)

        # Step 5: Put a log in the chatter of the newly-created accounts
        msg_body = _(
            "This account was split off from %(account_name)s (%(company_name)s).",
            account_name=self._get_html_link(title=self.display_name),
            company_name=base_company.name,
        )
        new_accounts._message_log_batch(bodies={a.id: msg_body for a in new_accounts})

        return new_accounts