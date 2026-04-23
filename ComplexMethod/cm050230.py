def _compute_payment_provider_id(self):
        results = self.journal_id._get_journals_payment_method_information()
        manage_providers = results['manage_providers']
        method_information_mapping = results['method_information_mapping']
        providers_per_code = results['providers_per_code']

        for line in self:
            journal = line.journal_id
            company = journal.company_id
            if (
                company
                and line.payment_method_id
                and not line.payment_provider_id
                and manage_providers
                and method_information_mapping.get(line.payment_method_id.id, {}).get('mode') == 'electronic'
            ):
                provider_ids = providers_per_code.get(company.id, {}).get(line.code, set())

                # Exclude the 'unique' / 'electronic' values that are already set on the journal.
                protected_provider_ids = set()
                for payment_type in ('inbound', 'outbound'):
                    lines = journal[f'{payment_type}_payment_method_line_ids']
                    for journal_line in lines:
                        if journal_line.payment_method_id:
                            if (
                                manage_providers
                                and method_information_mapping.get(journal_line.payment_method_id.id, {}).get('mode') == 'electronic'
                            ):
                                protected_provider_ids.add(journal_line.payment_provider_id.id)

                candidates_provider_ids = provider_ids - protected_provider_ids
                if candidates_provider_ids:
                    line.payment_provider_id = next(iter(candidates_provider_ids))