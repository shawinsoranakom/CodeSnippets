def _message_track(self, fields_iter, initial_values_dict):
        """ Track updated values. Comparing the initial and current values of
        the fields given in tracked_fields, it generates a message containing
        the updated values. This message can be linked to a mail.message.subtype
        given by the ``_track_subtype`` method.

        :param iter fields_iter: iterable of field names to track
        :param dict initial_values_dict: mapping {record_id: initial_values}
          where initial_values is a dict {field_name: value, ... }
        :return: mapping {record_id: (changed_field_names, tracking_value_ids)}
            containing existing records only
        """
        if not fields_iter:
            return {}

        tracked_fields = self.fields_get(fields_iter, attributes=('string', 'type', 'selection', 'currency_field'))
        tracking = dict()
        for record in self:
            try:
                tracking[record.id] = record._mail_track(tracked_fields, initial_values_dict[record.id])
            except MissingError:
                continue

        # find content to log as body
        bodies = self.env.cr.precommit.data.pop(f'mail.tracking.message.{self._name}', {})
        authors = self.env.cr.precommit.data.pop(f'mail.tracking.author.{self._name}', {})
        for record in self:
            changes, tracking_value_ids = tracking.get(record.id, (None, None))
            if not changes:
                continue

            # find subtypes and post messages or log if no subtype found
            subtype = record._track_subtype(
                dict((col_name, initial_values_dict[record.id][col_name])
                     for col_name in changes)
            )
            author_id = authors[record.id].id if record.id in authors else None
            # _set_log_message takes priority over _track_get_default_log_message even if it's an empty string
            body = bodies[record.id] if record.id in bodies else record._track_get_default_log_message(changes)
            if subtype:
                if not subtype.exists():
                    _logger.debug('subtype "%s" not found' % subtype.name)
                    continue
                record.message_post(
                    body=body,
                    author_id=author_id,
                    subtype_id=subtype.id,
                    tracking_value_ids=tracking_value_ids
                )
            elif tracking_value_ids:
                record._message_log(
                    body=body,
                    author_id=author_id,
                    tracking_value_ids=tracking_value_ids
                )

        return tracking