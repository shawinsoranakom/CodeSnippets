def _compute_available_payment_method_ids(self):
        """
        Compute the available payment methods id by respecting the following rules:
            Methods of mode 'unique' cannot be used twice on the same company.
            Methods of mode 'electronic' cannot be used twice on the same company for the same 'payment_provider_id'.
            Methods of mode 'multi' can be duplicated on the same journal.
        """
        results = self._get_journals_payment_method_information()
        pay_methods = results['pay_methods']
        manage_providers = results['manage_providers']
        method_information_mapping = results['method_information_mapping']
        providers_per_code = results['providers_per_code']

        journal_bank_cash = self.filtered(lambda j: j.type in ('bank', 'cash', 'credit'))
        journal_other = self - journal_bank_cash
        journal_other.available_payment_method_ids = False

        # Compute the candidates for each bank/cash journal.
        for journal in journal_bank_cash:
            commands = [Command.clear()]
            company = journal.company_id

            # Exclude the 'unique' / 'electronic' values that are already set on the journal.
            protected_provider_ids = set()
            protected_payment_method_ids = set()
            for payment_type in ('inbound', 'outbound'):
                lines = journal[f'{payment_type}_payment_method_line_ids']
                for line in lines:
                    if line.payment_method_id.id in method_information_mapping:
                        protected_payment_method_ids.add(line.payment_method_id.id)
                        if manage_providers and method_information_mapping.get(line.payment_method_id.id, {}).get('mode') == 'electronic':
                            protected_provider_ids.add(line.payment_provider_id.id)

            for pay_method in pay_methods:
                # Check the partial domain of the payment method to make sure the type matches the current journal
                if not journal._is_payment_method_available(pay_method.code, complete_domain=False):
                    continue

                values = method_information_mapping[pay_method.id]

                if values['mode'] == 'unique':
                    # 'unique' are linked to a single journal per company.
                    already_linked_journal_ids = set(values['company_journals'].get(company.id, [])) - {journal._origin.id}
                    if not already_linked_journal_ids and pay_method.id not in protected_payment_method_ids:
                        commands.append(Command.link(pay_method.id))
                elif manage_providers and values['mode'] == 'electronic':
                    # 'electronic' are linked to a single journal per company per provider.
                    for provider_id in providers_per_code.get(company.id, {}).get(pay_method.code, set()):
                        already_linked_journal_ids = set(values['company_journals'].get(company.id, {}).get(provider_id, [])) - {journal._origin.id}
                        if not already_linked_journal_ids and provider_id not in protected_provider_ids:
                            commands.append(Command.link(pay_method.id))
                elif values['mode'] == 'multi':
                    # 'multi' are unlimited.
                    commands.append(Command.link(pay_method.id))

            journal.available_payment_method_ids = commands