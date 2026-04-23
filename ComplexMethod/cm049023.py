def _get_query(self):
        name = self.name.strip()
        email = f"%{self.email.strip()}%"
        email_normalized = tools.email_normalize(self.email.strip())
        if not email_normalized:
            raise UserError(_('Invalid email address “%s”', self.email))

        # Step 1: Retrieve users/partners liked to email address or name
        query = SQL("""
            WITH indirect_references AS (
                SELECT id
                FROM res_partner
                WHERE email_normalized = %s
                OR name ilike %s)
            SELECT
                %s AS res_model_id,
                id AS res_id,
                active AS is_active
            FROM res_partner
            WHERE id IN (SELECT id FROM indirect_references)
            UNION ALL
            SELECT
                %s AS res_model_id,
                id AS res_id,
                active AS is_active
            FROM res_users
            WHERE (
                (login ilike %s)
                OR
                (partner_id IN (
                    SELECT id
                    FROM res_partner
                    WHERE email ilike %s or name ilike %s)))
            -- Step 2: Special case for direct messages
            UNION ALL
            SELECT
                %s AS res_model_id,
                id AS res_id,
                True AS is_active
            FROM mail_message
            WHERE author_id IN (SELECT id FROM indirect_references)
        """,
            # Indirect references CTE
            email_normalized, name,
            # Search on res.partner
            self.env['ir.model.data']._xmlid_to_res_id('base.model_res_partner'),
            # Search on res.users
            self.env['ir.model.data']._xmlid_to_res_id('base.model_res_users'), email, email, name,
            # Direct messages
            self.env['ir.model.data']._xmlid_to_res_id('mail.model_mail_message'),
        )

        # Step 3: Retrieve info on other models
        blacklisted_models = self._get_query_models_blacklist()
        for model_name in self.env:
            if model_name in blacklisted_models:
                continue

            model = self.env[model_name]
            if model._transient or not model._auto:
                continue

            table_name = model._table

            conditions = []
            # 3.1 Search Basic Personal Data Records (aka email/name usage)
            for field_name in ['email_normalized', 'email', 'email_from', 'company_email']:
                if field_name in model and model._fields[field_name].store:
                    rec_name = model._rec_name or 'name'
                    is_normalized = field_name == 'email_normalized' or (model_name == 'mailing.trace' and field_name == 'email')

                    conditions.append(SQL(
                        "%s %s %s",
                        SQL.identifier(field_name),
                        SQL('=') if is_normalized else SQL('ilike'),  # Manage Foo Bar <foo@bar.com>
                        email_normalized if is_normalized else email
                    ))
                    if rec_name in model and model._fields[model._rec_name].store and model._fields[model._rec_name].type == 'char' and not model._fields[model._rec_name].translate:
                        conditions.append(SQL(
                            "%s ilike %s",
                            SQL.identifier(rec_name),
                            name,
                        ))
                    if is_normalized:
                        break

            # 3.2 Search Indirect Personal Data References (aka partner_id)
            conditions.extend(
                SQL(
                    "%s in (SELECT id FROM indirect_references)",
                    model._field_to_sql(table_name, field_name),
                )
                for field_name, field in model._fields.items()
                if field.comodel_name == 'res.partner'
                if field.store
                if field.type == 'many2one'
                if field.ondelete != 'cascade'
            )

            if conditions:
                query = SQL("""
                    %s
                    UNION ALL
                    SELECT
                        %s AS res_model_id,
                        id AS res_id,
                        %s AS is_active
                    FROM %s
                    WHERE %s
                """,
                    query,
                    self.env['ir.model'].search([('model', '=', model_name)]).id,
                    SQL.identifier('active') if 'active' in model else True,
                    SQL.identifier(table_name),
                    SQL(" OR ").join(conditions),
                )
        return query