def create(self, vals_list):
        """ Create new (or activate existing) blacklisted numbers.
                A. Note: Attempt to create a number that already exists, but is non-active, will result in its activation.
                B. Note: If the number already exists and it's active, it will be added to returned set, (it won't be re-created)
        Returns Recordset union of created and existing phonenumbers from the requested list of numbers to create
        """
        # Extract and sanitize numbers, ensuring uniques
        to_create = []
        done = set()
        for value in vals_list:
            try:
                sanitized_value = self.env.user._phone_format(number=value['number'], raise_exception=True)
            except UserError as err:
                raise UserError(_("%(error)s Please correct the number and try again.", error=err)) from err
            if sanitized_value in done:
                continue
            done.add(sanitized_value)
            to_create.append(dict(value, number=sanitized_value))

        # Search for existing phone blacklist entries, even inactive ones (will be activated again)
        numbers_requested = [values['number'] for values in to_create]
        existing = self.with_context(active_test=False).search([('number', 'in', numbers_requested)])

        # Out of existing pb records, activate non-active, (unless requested to leave them alone with 'active' set to False)
        numbers_to_keep_inactive = {values['number'] for values in to_create if not values.get('active', True)}
        numbers_to_keep_inactive = numbers_to_keep_inactive & set(existing.mapped('number'))
        existing.filtered(lambda pb: not pb.active and pb.number not in numbers_to_keep_inactive).write({'active': True})

        # Create new records, while skipping existing_numbers
        existing_numbers = set(existing.mapped('number'))
        to_create_filtered = [values for values in to_create if values['number'] not in existing_numbers]
        created = super().create(to_create_filtered)

        # Preserve the original order of numbers requested to create
        numbers_to_id = {record.number: record.id for record in existing | created}
        return self.browse(numbers_to_id[number] for number in numbers_requested)