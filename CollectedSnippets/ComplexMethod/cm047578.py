def _check_company(self, fnames=None):
        """ Check the companies of the values of the given field names.

        :param list fnames: names of relational fields to check
        :raises UserError: if the `company_id` of the value of any field is not
            in `[False, self.company_id]` (or `self` if
            :class:`~odoo.addons.base.models.res_company`).

        For :class:`~odoo.addons.base.models.res_users` relational fields,
        verifies record company is in `company_ids` fields.

        User with main company A, having access to company A and B, could be
        assigned or linked to records in company B.
        """
        if fnames is None or {'company_id', 'company_ids'} & set(fnames):
            fnames = self._fields

        regular_fields = []
        property_fields = []
        for name in fnames:
            field = self._fields[name]
            if field.relational and field.check_company:
                if not field.company_dependent:
                    regular_fields.append(name)
                else:
                    property_fields.append(name)

        if not (regular_fields or property_fields):
            return

        inconsistencies = []
        for record in self:
            # The first part of the check verifies that all records linked via relation fields are compatible
            # with the company of the origin document, i.e. `self.account_id.company_id == self.company_id`
            if regular_fields:
                if self._name == 'res.company':
                    companies = record
                elif 'company_id' in self:
                    companies = record.company_id
                elif 'company_ids' in self:
                    companies = record.company_ids
                else:
                    _logger.warning(_(
                        "Skipping a company check for model %(model_name)s. Its fields %(field_names)s are set as company-dependent, "
                        "but the model doesn't have a `company_id` or `company_ids` field!",
                        model_name=self._name, field_names=regular_fields
                    ))
                    continue
                for name in regular_fields:
                    corecords = record.sudo()[name]
                    if corecords:
                        domain = corecords._check_company_domain(companies)
                        if domain and corecords != corecords.with_context(active_test=False).filtered_domain(domain):
                            inconsistencies.append((record, name, corecords))
            # The second part of the check (for property / company-dependent fields) verifies that the records
            # linked via those relation fields are compatible with the company that owns the property value, i.e.
            # the company for which the value is being assigned, i.e:
            #      `self.property_account_payable_id.company_id == self.env.company
            company = self.env.company
            for name in property_fields:
                corecords = record.sudo()[name]
                if corecords:
                    domain = corecords._check_company_domain(company)
                    if domain and corecords != corecords.with_context(active_test=False).filtered_domain(domain):
                        inconsistencies.append((record, name, corecords))

        if inconsistencies:
            lines = [_("Uh-oh! You’ve got some company inconsistencies here:")]
            company_msg = _lt("- Record is company “%(company)s” while “%(field)s” (%(fname)s: %(values)s) belongs to another company.")
            record_msg = _lt("- “%(record)s” belongs to company “%(company)s” while “%(field)s” (%(fname)s: %(values)s) belongs to another company.")
            root_company_msg = _lt("- Only a root company can be set on “%(record)s”. Currently set to “%(company)s”")
            for record, name, corecords in inconsistencies[:5]:
                if record._name == 'res.company':
                    msg, companies = company_msg, record
                elif record == corecords and name == 'company_id':
                    msg, companies = root_company_msg, record.company_id
                else:
                    msg = record_msg
                    companies = record.company_id if 'company_id' in record else record.company_ids
                field = self.env['ir.model.fields']._get(self._name, name)
                lines.append(str(msg) % {
                    'record': record.display_name,
                    'company': ", ".join(company.display_name for company in companies),
                    'field': field.field_description,
                    'fname': field.name,
                    'values': ", ".join(repr(rec.display_name) for rec in corecords),
                })
            lines.append(_("To avoid a mess, no company crossover is allowed!"))
            raise UserError("\n".join(lines))