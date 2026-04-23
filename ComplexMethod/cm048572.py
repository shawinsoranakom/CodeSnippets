def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default)
        code_by_company_id = {
            company_id: set(self.env['account.journal'].with_context(active_test=False)._read_group(
                domain=self.env['account.journal']._check_company_domain(company_id),
                aggregates=['code:array_agg'],
            )[0][0])
            for company_id, _ in groupby(vals_list, lambda v: v['company_id'])
        }
        for journal, vals in zip(self, vals_list):
            # Find a unique code for the copied journal
            all_journal_codes = code_by_company_id[vals['company_id']]

            copy_code = vals['code']
            code_prefix = re.sub(r'\d+', '', copy_code).strip()
            counter = 1
            while counter <= len(all_journal_codes) and copy_code in all_journal_codes:
                counter_str = str(counter)
                copy_prefix = code_prefix[:journal._fields['code'].size - len(counter_str)]
                copy_code = "%s%s" % (copy_prefix, counter_str)
                counter += 1

            if counter > len(all_journal_codes):
                # Should never happen, but put there just in case.
                raise UserError(_("Could not compute any code for the copy automatically. Please create it manually."))

            vals.update(
                code=copy_code,
                name=_("%s (copy)", journal.name or ''))
        return vals_list