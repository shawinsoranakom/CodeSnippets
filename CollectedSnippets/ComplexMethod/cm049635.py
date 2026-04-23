def _get_visitor_from_request(self, force_create=False, force_track_values=None):
        """ Return the visitor as sudo from the request.

        :param force_create: force a visitor creation if no visitor exists
        :param force_track_values: an optional dict to create a track at the
            same time.
        :return: the website visitor if exists or forced, empty recordset
            otherwise.
        """

        # This function can be called in json with mobile app.
        # In case of mobile app, no uid is set on the jsonRequest env.
        # In case of multi db, _env is None on request, and request.env unbound.
        if not (request and request.env and request.env.uid):
            return None

        access_token = self._get_access_token()

        if force_create:
            visitor_id, _ = self._upsert_visitor(access_token, force_track_values)
            return self.env['website.visitor'].sudo().browse(visitor_id)

        visitor = self.env['website.visitor'].sudo().search_fetch([('access_token', '=', access_token)])

        if not force_create and not self.env.cr.readonly and visitor and not visitor.timezone:
            tz = self._get_visitor_timezone()
            if tz:
                visitor._update_visitor_timezone(tz)

        return visitor