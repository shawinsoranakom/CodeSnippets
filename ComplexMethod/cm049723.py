def get(self, service_name, force_create=True):
        domain = [
            ('service_name', '=', service_name),
            '|',
                ('company_ids', 'in', self.env.companies.ids),
                ('company_ids', '=', False)
        ]
        accounts = self.search(domain, order='id desc')
        accounts_without_token = accounts.filtered(lambda acc: not acc.sudo().account_token)
        if accounts_without_token:
            with self.pool.cursor() as cr:
                # In case of a further error that will rollback the database, we should
                # use a different SQL cursor to avoid undo the accounts deletion.

                # Flush the pending operations to avoid a deadlock.
                self.env.flush_all()
                IapAccount = self.with_env(self.env(cr=cr))
                # Need to use sudo because regular users do not have delete right
                IapAccount.search(domain + [('account_token', '=', False)]).sudo().unlink()
                accounts = accounts - accounts_without_token
        if not accounts:
            service = self.env['iap.service'].search([('technical_name', '=', service_name)], limit=1)
            if not service:
                raise UserError(self.env._("No service exists with the provided technical name"))
            if module.current_test:
                # During testing, we don't want to commit the creation of a new IAP account to the database
                return self.sudo().create({'service_id': service.id})

            with self.pool.cursor() as cr:
                # Since the account did not exist yet, we will encounter a NoCreditError,
                # which is going to rollback the database and undo the account creation,
                # preventing the process to continue any further.

                # Flush the pending operations to avoid a deadlock.
                self.env.flush_all()
                IapAccount = self.with_env(self.env(cr=cr))
                account = IapAccount.search(domain, order='id desc', limit=1)
                if not account:
                    if not force_create:
                        return account
                    account = IapAccount.create({'service_id': service.id})
                # fetch 'account_token' into cache with this cursor,
                # as self's cursor cannot see this account
                account_token = account.sudo().account_token
            account = self.browse(account.id)
            self.env.cache.set(account, IapAccount._fields['account_token'], account_token)
            return account
        accounts_with_company = accounts.filtered(lambda acc: acc.company_ids)
        if accounts_with_company:
            return accounts_with_company[0]
        return accounts[0]