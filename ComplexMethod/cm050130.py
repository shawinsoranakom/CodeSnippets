def _check_mailing_email_token(self, mailing_id, document_id, email, hash_token,
                                   required_mailing_id=False):
        """ Return the mailing based on given credentials, sudo-ed. Raises if
        there is an issue fetching it.

        Specific use case
          * hash_token is always required for public users, no generic page is
            available for them;
          * hash_token is not required for generic page for logged user, aka
            if no mailing_id is given;
          * hash_token is not required for mailing specific page if the user
            is a mailing user;
          * hash_token is not required for generic page for logged user, aka
            if no mailing_id is given and if mailing_id is not required;
          * hash_token always requires the triplet mailing_id, email and
            document_id, as it indicates it comes from a mailing email and
            is used when comparing hashes;
        """
        if not hash_token:
            if request.env.user._is_public():
                raise BadRequest()
            if mailing_id and not request.env.user.has_group('mass_mailing.group_mass_mailing_user'):
                raise BadRequest()
        if hash_token and (not mailing_id or not email or not document_id):
            raise BadRequest()
        if mailing_id:
            mailing_sudo = request.env['mailing.mailing'].sudo().browse(mailing_id)
            if not mailing_sudo.exists():
                raise NotFound()
            if hash_token and not consteq(mailing_sudo._generate_mailing_recipient_token(document_id, email), hash_token):
                raise Unauthorized()
        else:
            if required_mailing_id:
                raise BadRequest()
            mailing_sudo = request.env['mailing.mailing'].sudo()
        return mailing_sudo