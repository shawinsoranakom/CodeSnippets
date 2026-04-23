def _description_domain(self, env: Environment) -> str | list:
        domain = self._internal_description_domain_raw(env)
        if self.check_company:
            field_to_check = None
            if self.company_dependent:
                cids = '[allowed_company_ids[0]]'
            elif self.model_name == 'res.company':
                # when using check_company=True on a field on 'res.company', the
                # company_id comes from the id of the current record
                cids = '[id]'
            elif 'company_id' in env[self.model_name]:
                cids = '[company_id]'
                field_to_check = 'company_id'
            elif 'company_ids' in env[self.model_name]:
                cids = 'company_ids'
                field_to_check = 'company_ids'
            else:
                _logger.warning(env._(
                    "Couldn't generate a company-dependent domain for field %s. "
                    "The model doesn't have a 'company_id' or 'company_ids' field, and isn't company-dependent either.",
                    self.model_name + '.' + self.name,
                ))
                return domain
            company_domain = env[self.comodel_name]._check_company_domain(companies=unquote(cids))
            if not field_to_check:
                return f"{company_domain} + {domain or []}"
            else:
                no_company_domain = env[self.comodel_name]._check_company_domain(companies='')
                return f"({field_to_check} and {company_domain} or {no_company_domain}) + ({domain or []})"
        return domain