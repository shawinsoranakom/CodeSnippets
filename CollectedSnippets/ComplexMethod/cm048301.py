def _compute_event_booth_ids(self):
        """ Update event configuration from its event type. Depends are set only
        on event_type_id itself, not its sub fields. Purpose is to emulate an
        onchange: if event type is changed, update event configuration. Changing
        event type content itself should not trigger this method.

        When synchronizing booths:

          * lines that are available are removed;
          * template lines are added;
        """
        for event in self:
            if not event.event_type_id and not event.event_booth_ids:
                event.event_booth_ids = False
                continue

            # booths to keep: those that are not available
            booths_to_remove = event.event_booth_ids.filtered(lambda booth: booth.is_available)
            command = [Command.unlink(booth.id) for booth in booths_to_remove]
            if event.event_type_id.event_type_booth_ids:
                command += [
                    Command.create({
                        attribute_name: line[attribute_name] if not isinstance(line[attribute_name], models.BaseModel) else line[attribute_name].id
                        for attribute_name in self.env['event.type.booth']._get_event_booth_fields_whitelist()
                    }) for line in event.event_type_id.event_type_booth_ids
                ]
            event.event_booth_ids = command