def _check_payment_method_line_ids_multiplicity(self):
        """
        Check and ensure that the payment method lines multiplicity is respected.
        """
        results = self._get_journals_payment_method_information()
        pay_methods = results['pay_methods']
        manage_providers = results['manage_providers']
        method_information_mapping = results['method_information_mapping']
        providers_per_code = results['providers_per_code']

        failing_unicity_payment_methods = self.env['account.payment.method']
        for journal in self:
            company = journal.company_id

            # Exclude the 'unique' / 'electronic' values that are already set on the journal.
            protected_provider_ids = set()
            protected_payment_method_ids = set()
            for payment_type in ('inbound', 'outbound'):
                lines = journal[f'{payment_type}_payment_method_line_ids']

                # Ensure you don't have the same payment_method/name combination twice on the same journal.
                counter = {}
                for line in lines:
                    if method_information_mapping.get(line.payment_method_id.id, {}).get('mode') not in ('electronic', 'unique'):
                        continue

                    key = line.payment_method_id.id, line.name
                    counter.setdefault(key, 0)
                    counter[key] += 1
                    if counter[key] > 1:
                        raise ValidationError(_(
                            "You can't have two payment method lines of the same payment type (%(payment_type)s) "
                            "and with the same name (%(name)s) on a single journal.",
                            payment_type=payment_type,
                            name=line.name,
                        ))

                for line in lines:
                    if line.payment_method_id.id in method_information_mapping:
                        protected_payment_method_ids.add(line.payment_method_id.id)
                        if manage_providers and method_information_mapping[line.payment_method_id.id]['mode'] == 'electronic':
                            protected_provider_ids.add(line.payment_provider_id.id)

            for pay_method in pay_methods:
                values = method_information_mapping[pay_method.id]

                if values['mode'] == 'unique':
                    # 'unique' are linked to a single journal per company.
                    already_linked_journal_ids = values['company_journals'].get(company.id, [])
                    if len(already_linked_journal_ids) > 1:
                        failing_unicity_payment_methods |= pay_method
                elif manage_providers and values['mode'] == 'electronic':
                    # 'electronic' are linked to a single journal per company per provider.
                    for provider_id in providers_per_code.get(company.id, {}).get(pay_method.code, set()):
                        already_linked_journal_ids = values['company_journals'].get(company.id, {}).get(provider_id, [])
                        if len(already_linked_journal_ids) > 1:
                            failing_unicity_payment_methods |= pay_method

        if failing_unicity_payment_methods:
            raise ValidationError(_(
                "Some payment methods supposed to be unique already exists somewhere else.\n(%s)",
                ', '.join(failing_unicity_payment_methods.mapped('display_name')),
            ))