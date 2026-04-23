def _alias_get_error(self, message, message_dict, alias):
        """ Generic method that takes a record not necessarily inheriting from
        mail.alias.mixin.

        :return: error if any, False otherwise
        :rtype: AliasError | Literal[False]
        """
        author = self.env['res.partner'].browse(message_dict.get('author_id', False))
        if alias.alias_contact == 'followers':
            if not self.ids:
                return AliasError('config_follower_no_record',
                                  _('incorrectly configured alias (unknown reference record)'),
                                  is_config_error=True)
            if not hasattr(self, "message_partner_ids"):
                return AliasError('config_follower_no_partners', _('incorrectly configured alias'), True)
            if not author or author not in self.message_partner_ids:
                return AliasError('error_follower_not_following', _('restricted to followers'))
        elif alias.alias_contact == 'partners' and not author:
            return AliasError('error_partners_no_partner', _('restricted to known authors'))
        return False