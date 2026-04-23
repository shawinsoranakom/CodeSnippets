def _map_eu_taxes(self):
        '''Creates or updates Fiscal Positions for each EU country excluding the company's account_fiscal_country_id
        '''
        eu_countries = self.env.ref('base.europe').country_ids
        oss_tax_groups = self.env['ir.model.data'].search([
            ('name', 'ilike', 'oss_tax_group'),
            ('module', '=', 'account'),
            ('model', '=', 'account.tax.group')])
        for company in self:
            # instantiate OSS taxes on the first branch with a TAX ID, default on root company
            company = company.parent_ids.filtered(lambda c: c.vat)[-1:] or company.root_id
            invoice_repartition_lines, refund_repartition_lines = company._get_repartition_lines_oss()
            taxes = self.env['account.tax'].search([
                *self.env['account.tax']._check_company_domain(company),
                ('type_tax_use', '=', 'sale'),
                ('amount_type', '=', 'percent'),
                ('tax_group_id', 'not in', oss_tax_groups.mapped('res_id'))
            ])

            multi_tax_reports_countries_fpos = self.env['account.fiscal.position'].search([
                ('foreign_vat', '!=', False),
            ])
            oss_countries = eu_countries - company.account_fiscal_country_id - multi_tax_reports_countries_fpos.country_id
            tg = self.env['account.tax.group'].search([
                *self.env['account.tax.group']._check_company_domain(company),
                ('tax_payable_account_id', '!=', False),
                ('tax_receivable_account_id', '!=', False)], limit=1)
            if not tg:
                raise RedirectWarning(
                    self.env._("To properly configure OSS tax mapping, the domestic tax group you are using must have the necessary accounts defined."),
                    self.env['account.tax.group'].search(self.env['account.tax.group']._check_company_domain(company))._get_records_action(name=self.env._("Tax Groups")),
                    self.env._("View Tax Groups"),
                )
            default_oss_payable_account = self.env['account.account']

            eu_vat_country_group_id = self.env.ref('account.europe_vat').id
            eu_b2c_fp = self.env['account.fiscal.position'].search([
                ('company_id', '=', company.id),
                ('country_group_id', '=', eu_vat_country_group_id),
                ('auto_apply', '=', True),
                ('vat_required', '=', False),
            ], limit=1)
            offset = 1
            if eu_b2c_fp:
                # oss fp must come before eu b2c fp
                oss_fp_sequence = eu_b2c_fp.sequence
                to_bump = eu_b2c_fp | self.env['account.fiscal.position'].search([
                    ('company_id', '=', company.id),
                    ('sequence', '>', oss_fp_sequence),
                ])
            else:
                eu_b2b_fp = self.env['account.fiscal.position'].search([
                    ('company_id', '=', company.id),
                    ('country_group_id', '=', eu_vat_country_group_id),
                    ('auto_apply', '=', True),
                    ('vat_required', '=', True),
                ], limit=1)
                if eu_b2b_fp:
                    # oss fp must come after eu b2b fp
                    oss_fp_sequence = eu_b2b_fp.sequence + 1
                    offset = 2
                    to_bump = self.env['account.fiscal.position'].search([
                        ('company_id', '=', company.id),
                        ('sequence', '>', eu_b2b_fp.sequence),
                    ])
                else:
                    oss_fp_sequence = self.env['account.fiscal.position'].search([
                        ('company_id', '=', company.id)],
                        limit=1, order='sequence desc',
                    ).sequence + 1
                    to_bump = []
            for fp in to_bump:
                fp.sequence += offset

            for destination_country in oss_countries:
                mapping = []
                fpos = self.env['account.fiscal.position'].search([
                            ('company_id', '=', company.id),
                            ('country_id', '=', destination_country.id),
                            ('auto_apply', '=', True),
                            ('vat_required', '=', False),
                            ('foreign_vat', '=', False)], limit=1)
                if not fpos:
                    fpos = self.env['account.fiscal.position'].create({
                        'name': f'OSS B2C {destination_country.name}',
                        'country_id': destination_country.id,
                        'company_id': company.id,
                        'auto_apply': True,
                        'sequence': oss_fp_sequence,
                    })

                foreign_taxes = {tax.amount: tax for tax in fpos.tax_ids if tax.amount_type == 'percent'}

                for domestic_tax in taxes:
                    tax_amount = EU_TAX_MAP.get((domestic_tax.country_id.code, domestic_tax.amount, destination_country.code), False)
                    if tax_amount and domestic_tax not in fpos.tax_ids.original_tax_ids:
                        if not foreign_taxes.get(tax_amount, False):
                            oss_tax_group_local_xml_id = f"{company.id}_oss_tax_group_{str(tax_amount).replace('.', '_')}_{company.account_fiscal_country_id.code}"
                            if not self.env.ref(f"account.{oss_tax_group_local_xml_id}", raise_if_not_found=False):
                                if not default_oss_payable_account:
                                    default_oss_payable_account = self.env['account.account'].create([{
                                        'name': f'{tg.tax_payable_account_id.name} OSS',
                                        'code': self.env['account.account']._search_new_account_code(tg.tax_payable_account_id.with_company(company).code),
                                        'account_type': tg.tax_payable_account_id.account_type,
                                        'reconcile': tg.tax_payable_account_id.reconcile,
                                        'non_trade': tg.tax_payable_account_id.non_trade,
                                        'company_ids': [Command.link(company.id)],
                                    }])
                                    default_oss_receivable_account = self.env['account.account'].create([{
                                        'name': f'{tg.tax_receivable_account_id.name} OSS',
                                        'code': self.env['account.account']._search_new_account_code(tg.tax_receivable_account_id.with_company(company).code),
                                        'account_type': tg.tax_receivable_account_id.account_type,
                                        'reconcile': tg.tax_receivable_account_id.reconcile,
                                        'non_trade': tg.tax_receivable_account_id.non_trade,
                                        'company_ids': [Command.link(company.id)],
                                    }])

                                self.env['ir.model.data'].create({
                                    'name': oss_tax_group_local_xml_id,
                                    'module': 'account',
                                    'model': 'account.tax.group',
                                    'res_id': self.env['account.tax.group'].create({
                                        'name': f'OSS {tax_amount}%',
                                        'country_id': company.account_fiscal_country_id.id,
                                        'company_id': company.id,
                                        'tax_payable_account_id': default_oss_payable_account.id,
                                        'tax_receivable_account_id': default_oss_receivable_account.id,
                                    }).id,
                                    'noupdate': True,
                                })
                            foreign_tax_name = f'{tax_amount}% {destination_country.code} {destination_country.vat_label}'
                            existing_foreign_tax = self.env['account.tax'].search([
                                ('company_id', 'child_of', company.root_id.id),
                                ('name', 'like', foreign_tax_name),
                                ('type_tax_use', '=', 'sale'),
                                ('country_id', '=', company.account_fiscal_country_id.id),
                            ], order='sequence,id desc', limit=1)
                            foreign_tax_copy_name = existing_foreign_tax and _('%(tax_name)s (Copy)', tax_name=existing_foreign_tax.name)

                            extra_fields = company._get_country_specific_account_tax_fields()
                            foreign_taxes[tax_amount] = self.env['account.tax'].create({
                                'name': foreign_tax_copy_name or foreign_tax_name,
                                'amount': tax_amount,
                                'invoice_repartition_line_ids': invoice_repartition_lines,
                                'refund_repartition_line_ids': refund_repartition_lines,
                                'type_tax_use': 'sale',
                                'description': f"{tax_amount}%",
                                'tax_group_id': self.env.ref(f'account.{oss_tax_group_local_xml_id}').id,
                                'country_id': company.account_fiscal_country_id.id,
                                'sequence': 1000,
                                'company_id': company.id,
                                'fiscal_position_ids': [Command.link(fpos.id)],
                                'original_tax_ids': [Command.link(domestic_tax.id)],
                                **extra_fields,
                            })