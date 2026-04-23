def default_get(self, fields):
        """If we're creating a new account through a many2one, there are chances that we typed the account code
        instead of its name. In that case, switch both fields values.
        """
        context = {}
        if 'name' in fields or 'code' in fields:
            default_name = self.env.context.get('default_name')
            default_code = self.env.context.get('default_code')
            if default_name and not default_code:
                with contextlib.suppress(ValueError):
                    default_code = int(default_name)
                if default_code:
                    default_name = False
                context.update({'default_name': default_name, 'default_code': default_code})

        defaults = super(AccountAccount, self.with_context(**context)).default_get(fields)

        if 'code_mapping_ids' in fields and 'code_mapping_ids' not in defaults:
            defaults['code_mapping_ids'] = [Command.create({'company_id': c.id}) for c in self.env.user.company_ids]

        return defaults