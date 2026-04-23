def _message_parse_post_process(self, message, message_dict, routes):
        """ Parse and process incoming email values that are better computed
        based on record we are about to create or update. This refers to
        message author and recipients, which can be preferentially found
        in document followers when possible. """
        values = {
            'author_id': message_dict.get('author_id'),
            'partner_ids': message_dict.get('partner_ids'),
        }
        for model, thread_id, _custom_values, _user_id, alias in routes or ():
            link_doc = self.env[model].browse(thread_id) if thread_id else self.env[model]
            if not link_doc and alias and alias.alias_parent_model_id and alias.alias_parent_thread_id:
                link_doc = self.env[alias.alias_parent_model_id.model].browse(alias.alias_parent_thread_id)
            link_doc = link_doc if link_doc and hasattr(link_doc, '_partner_find_from_emails_single') else self.env['mail.thread']

            if not values.get('author_id') and message_dict['email_from']:
                author = link_doc._partner_find_from_emails_single([message_dict['email_from']], no_create=True)
                if author:
                    values['author_id'] = author.id
            if not values.get('partner_ids') and message_dict['recipients']:
                values['partner_ids'] = link_doc._partner_find_from_emails_single(email_split(message_dict['recipients']), no_create=True).ids
        return values