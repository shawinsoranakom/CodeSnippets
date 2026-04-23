def _pre_reload_data(self, company, template_data, data, force_create=True):
        """Pre-process the data in case of reloading the chart of accounts.

        When we reload the chart of accounts, we only want to update fields that are main
        configuration, like:
        - tax tags
        """
        for prop in list(template_data):
            if prop.startswith('property_'):
                template_data.pop(prop)
        data.pop('account.reconcile.model', None)
        if 'res.company' in data:
            data['res.company'][company.id].clear()
            data['res.company'][company.id].setdefault('anglo_saxon_accounting', company.anglo_saxon_accounting)
        for xmlid, journal_data in list(data.get('account.journal', {}).items()):
            if self.ref(xmlid, raise_if_not_found=False):
                del data['account.journal'][xmlid]
            else:
                journal = None
                lang = self._get_untranslatable_fields_target_language(company.chart_template, company)
                translated_code = self._get_field_translation(journal_data, 'code', lang)
                if 'code' in journal_data:
                    journal_code = translated_code or journal_data['code']
                    journal = self.env['account.journal'].with_context(active_test=False).search([
                        *self.env['account.journal']._check_company_domain(company),
                        ('code', '=', journal_code),
                    ])
                # Try to match by journal name to avoid conflict in the unique constraint on the mail alias
                translated_name = self._get_field_translation(journal_data, 'name', lang)
                if not journal and 'name' in journal_data and 'type' in journal_data:
                    journal = self.env['account.journal'].with_context(active_test=False).search([
                        *self.env['account.journal']._check_company_domain(company),
                        ('type', '=', journal_data['type']),
                        ('name', 'in', (journal_data['name'], translated_name)),
                    ], limit=1)
                if journal:
                    del data['account.journal'][xmlid]
                    self.env['ir.model.data']._update_xmlids([{
                        'xml_id': self.company_xmlid(xmlid, company),
                        'record': journal,
                        'noupdate': True,
                    }])

        account_group_count = self.env['account.group'].search_count(
            [] if company.parent_id else [('company_id', '=', company.id)],
        )
        if account_group_count:
            data.pop('account.group', None)

        current_taxes = self.env['account.tax'].with_context(active_test=False).search([
            *self.env['account.tax']._check_company_domain(company),
        ])

        current_fiscal_positions =  self.env['account.fiscal.position'].with_context(active_test=False).search([
            *self.env['account.fiscal.position']._check_company_domain(company),
        ])

        current_tax_groups = self.env['account.tax.group'].with_context(active_test=False).search([
            *self.env['account.tax.group']._check_company_domain(company)
        ])

        unique_tax_name_key = lambda t: (t.name, t.type_tax_use, t.tax_scope, t.company_id)
        unique_tax_name_keys = set(current_taxes.mapped(unique_tax_name_key))
        xmlid2tax = {
            xml_id.split('.')[1].split('_', maxsplit=1)[1]: self.env['account.tax'].browse(record)
            for record, xml_id in current_taxes.get_external_id().items() if xml_id.startswith('account.')
        }
        xmlid2fiscal_position= {
            xml_id.split('.')[1].split('_', maxsplit=1)[1]: self.env['account.fiscal.position'].browse(record)
            for record, xml_id in current_fiscal_positions.get_external_id().items() if xml_id.startswith('account.')
        }
        xmlid2tax_group = {
            xml_id.split('.')[1].split('_', maxsplit=1)[1]: self.env['account.tax.group'].browse(res_id)
            for res_id, xml_id in current_tax_groups.get_external_id().items() if xml_id.startswith('account.')
        }
        def tax_template_changed(tax, template):
            template_line_ids = [x for x in template.get('repartition_line_ids', []) if x[0] != Command.CLEAR]
            return (
                tax.amount_type != template.get('amount_type', 'percent')
                or float_compare(tax.amount, template.get('amount', 0), precision_digits=4) != 0
                # Taxes that don't have repartition lines in their templates get theirs created by default
                or len(template_line_ids) not in (0, len(tax.repartition_line_ids))
            )

        obsolete_xmlid = set()
        skip_update = set()
        for model_name, records in data.items():
            for xmlid, values in records.items():
                if model_name == 'account.fiscal.position':
                    # if xmlid is not in xmlid2fiscal_position and we do not force create so we will skip_update for that record
                    if xmlid not in xmlid2fiscal_position:
                        if not force_create:
                            skip_update.add((model_name, xmlid))
                        continue
                    # Only add accounts mappings containing new records
                    if not force_create:  # there can't be new records if we don't create them
                        values.pop('account_ids', [])
                    if old_ids := values.pop('account_ids', []):
                        new_ids = []
                        for element in old_ids:
                            match element:
                                case Command.CREATE, _, {'account_src_id': src_id, 'account_dest_id': dest_id} if (
                                    not self.ref(src_id, raise_if_not_found=False)
                                    or (dest_id and not self.ref(dest_id, raise_if_not_found=False))
                                ):
                                    new_ids.append(element)
                        if new_ids:
                            values['account_ids'] = new_ids

                elif model_name == 'account.tax.group':
                    if xmlid not in xmlid2tax_group and not force_create:
                        skip_update.add((model_name, xmlid))
                        continue
                    if xmlid in xmlid2tax_group:
                        for field_name in ["tax_payable_account_id", "tax_receivable_account_id"]:
                            if field_name in values and self.ref(values[field_name], raise_if_not_found=False):
                                values.pop(field_name, None)

                elif model_name == 'account.tax':
                    if xmlid not in xmlid2tax or tax_template_changed(xmlid2tax[xmlid], values):
                        if not force_create:
                            skip_update.add((model_name, xmlid))
                            continue
                        if self.env.context.get('force_new_tax_active'):
                            values['active'] = True
                        if xmlid in xmlid2tax:
                            obsolete_xmlid.add(xmlid)
                            oldtax = xmlid2tax[xmlid]
                        else:
                            oldtax = current_taxes.filtered(
                                lambda t: t.name == values.get('name')\
                                      and t.type_tax_use == values.get('type_tax_use')\
                                      and t.tax_scope == values.get('tax_scope', False)
                            )
                        uniq_key = unique_tax_name_key(oldtax[0] if len(oldtax) > 1 else oldtax)
                        matching_names = len(list(filter(lambda t: re.match(fr"^(?:\[old\d*\] |){uniq_key[0]}$", t[0]) and t[1:] == uniq_key[1:], unique_tax_name_keys)))
                        for index, tax_to_rename in enumerate(oldtax):
                            rename_idx = index + matching_names
                            if rename_idx:
                                tax_to_rename.name = f"[old{rename_idx - 1 if rename_idx > 1 else ''}] {tax_to_rename.name}"
                    else:
                        fiscal_position_ids = values.get('fiscal_position_ids')
                        original_tax_ids = values.get('original_tax_ids')
                        repartition_lines = values.get('repartition_line_ids')
                        values.clear()
                        # taxes will always be (re)linked to fiscal positions (unless the fp doesn't exist and won't be created)
                        if fiscal_position_ids:
                            link_commands = [
                                Command.link(xml_id)
                                for xml_id in fiscal_position_ids.split(',') if force_create or xml_id in xmlid2fiscal_position
                            ]
                            if link_commands:
                                values['fiscal_position_ids'] = link_commands
                        # Only add tax mappings containing new taxes
                        if (
                            force_create
                            and original_tax_ids
                            and (new_taxes := [xml_id for xml_id in original_tax_ids.split(',') if xml_id not in xmlid2tax])
                        ):
                            values['original_tax_ids'] = [
                                Command.link(alt_xml_id)
                                for alt_xml_id in new_taxes
                            ]
                        if repartition_lines:
                            values['repartition_line_ids'] = repartition_lines
                            for element in values.get('repartition_line_ids', []):
                                match element:
                                    case int() as command, _, {'tag_ids': tags} as repartition_line_values if command in tuple(Command):
                                        repartition_line_values.clear()
                                        repartition_line_values['tag_ids'] = tags or [Command.clear()]
                elif model_name == 'account.account':
                    # Point or create xmlid to existing record to avoid duplicate code
                    account = self.ref(xmlid, raise_if_not_found=False)
                    normalized_code = f'{values["code"]:<0{int(template_data.get("code_digits", 6))}}'
                    if not account or not re.match(f'^{values["code"]}0*$', account.code):
                        query = self.env['account.account']._search(self.env['account.account']._check_company_domain(company))
                        account_code = self.with_company(company).env['account.account']._field_to_sql('account_account', 'code', query)
                        query.add_where(SQL("%s SIMILAR TO %s", account_code, f'{values["code"]}0*'))
                        accounts = self.env['account.account'].browse(query)
                        existing_account = accounts.sorted(key=lambda x: x.code != normalized_code)[0] if accounts else None
                        if existing_account:
                            self.env['ir.model.data']._update_xmlids([{
                                'xml_id': self.company_xmlid(xmlid, company),
                                'record': existing_account,
                                'noupdate': True,
                            }])
                            account = existing_account

                    # Prevents overriding user setting & raising a partial reconcile error.
                    values.pop('reconcile', None)
                    # on existing accounts, only tag_ids are to be updated using default data
                    if account and 'tag_ids' in data[model_name][xmlid]:
                        data[model_name][xmlid] = {'tag_ids': data[model_name][xmlid]['tag_ids']}
                    elif account or not force_create:
                        skip_update.add((model_name, xmlid))

        for skip_model, skip_xmlid in skip_update:
            data[skip_model].pop(skip_xmlid, None)

        if obsolete_xmlid:
            self.env['ir.model.data'].search([
                ('name', 'in', [f"{company.id}_{xmlid}" for xmlid in obsolete_xmlid]),
                ('module', '=', 'account'),
            ]).unlink()

        for model_name, records in data.items():
            _fields = self.env[model_name]._fields
            for xmlid, values in records.items():
                x2manyfields = [
                    fname
                    for fname in values
                    if fname in _fields
                    and _fields[fname].type in ('one2many', 'many2many')
                    and isinstance(values[fname], (list, tuple))
                ]
                if x2manyfields:
                    if isinstance(xmlid, int):
                        rec = self.env[model_name].browse(xmlid).exists()
                    else:
                        rec = self.ref(xmlid, raise_if_not_found=False)
                    if rec:
                        for fname in x2manyfields:
                            for i, (line, (command, _id, vals)) in enumerate(zip(rec[fname], values[fname])):
                                if command == Command.CREATE:  # converts ORM command `create` into `update`
                                    values[fname][i] = Command.update(line.id, vals)