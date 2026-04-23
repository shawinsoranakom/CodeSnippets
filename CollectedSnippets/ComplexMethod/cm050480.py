def _preprocess_x2many_vals_from_settings_view(self, vals):
        """ From the res.config.settings view, changes in the x2many fields always result to an array of link commands or a single set command.
            - As a result, the items that should be unlinked are not properly unlinked.
            - So before doing the write, we inspect the commands to determine which records should be unlinked.
            - We only care about the link command.
            - We can consider set command as absolute as it will replace all.
        """
        from_settings_view = self.env.context.get('from_settings_view')
        if not from_settings_view:
            # If vals is not from the settings view, we don't need to preprocess.
            return

        # Only ensure one when write is from settings view.
        self.ensure_one()

        fields_to_preprocess = []
        for f in self.fields_get([]).values():
            if f['type'] in ['many2many', 'one2many']:
                fields_to_preprocess.append(f['name'])

        for x2many_field in fields_to_preprocess:
            if x2many_field in vals:
                linked_ids = set(self[x2many_field].ids)

                for command in vals[x2many_field]:
                    if command[0] == 4:
                        _id = command[1]
                        if _id in linked_ids:
                            linked_ids.remove(_id)

                # Remaining items in linked_ids should be unlinked.
                unlink_commands = [Command.unlink(_id) for _id in linked_ids]

                vals[x2many_field] = unlink_commands + vals[x2many_field]