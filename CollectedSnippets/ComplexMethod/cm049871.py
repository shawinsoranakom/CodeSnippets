def _message_track_post_template(self, changes):
        """ Based on a tracking, post a message defined by ``_track_template``
        parameters. It allows to implement automatic post of messages based
        on templates (e.g. stage change triggering automatic email).

        :param dict changes: mapping {record_id: (changed_field_names, tracking_value_ids)}
            containing existing records only
        """
        if not self or not changes:
            return True
        # Clean the context to get rid of residual default_* keys
        # that could cause issues afterward during the mail.message
        # generation. Example: 'default_parent_id' would refer to
        # the parent_id of the current record that was used during
        # its creation, but could refer to wrong parent message id,
        # leading to a traceback in case the related message_id
        # doesn't exist
        cleaned_self = self.with_context(clean_context(self.env.context))._fallback_lang()
        try:
            templates = self._track_template(changes)
        except MissingError:
            if not self.exists():
                return
            raise

        default_composition_mode = 'mass_mail' if len(self) != 1 else 'comment'
        for (template, post_kwargs) in templates.values():
            if not template:
                continue

            composition_mode = post_kwargs.pop('composition_mode', default_composition_mode)
            post_kwargs.setdefault('message_type', 'auto_comment')
            # by default, allow sending stage updates to author
            post_kwargs.setdefault('notify_author_mention', True)
            if composition_mode == 'mass_mail':
                cleaned_self.message_mail_with_source(template, **post_kwargs)
            else:
                cleaned_self.message_post_with_source(template, **post_kwargs)
        return True