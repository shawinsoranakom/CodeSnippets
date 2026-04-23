def _check_nilvera_customer(self):
        self.ensure_one()
        if not self.vat:
            return

        with _get_nilvera_client(self.env.company) as client:
            response = client.request("GET", "/general/GlobalCompany/Check/TaxNumber/" + urllib.parse.quote(self.vat), handle_response=False)
            if response.status_code == 200:
                query_result = response.json()

                if not query_result:
                    self.l10n_tr_nilvera_customer_status = 'earchive'
                    self.l10n_tr_nilvera_customer_alias_id = False
                else:
                    self.l10n_tr_nilvera_customer_status = 'einvoice'

                    # We need to sync the data from the API with the records in database.
                    aliases = {result.get('Name') for result in query_result}
                    persisted_aliases = self.l10n_tr_nilvera_customer_alias_ids
                    # Find aliases to add (in query result but not in database).
                    aliases_to_add = aliases - set(persisted_aliases.mapped('name'))
                    # Find aliases to remove (in database but not in query result).
                    aliases_to_remove = set(persisted_aliases.mapped('name')) - aliases

                    newly_persisted_aliases = self.env['l10n_tr.nilvera.alias'].create([{
                        'name': alias_name,
                        'partner_id': self.id,
                    } for alias_name in aliases_to_add])
                    to_keep = persisted_aliases.filtered(lambda a: a.name not in aliases_to_remove)
                    (persisted_aliases - to_keep).unlink()

                    # If no alias was previously selected, automatically select the first alias.
                    remaining_aliases = newly_persisted_aliases | to_keep
                    if not self.l10n_tr_nilvera_customer_alias_id and remaining_aliases:
                        self.l10n_tr_nilvera_customer_alias_id = remaining_aliases[0]
                # commit the result of each request because in the case of a bulk verify the
                # server can timeout and all progress will be undone
                self.env.cr.commit()
                return True
            else:
                return False