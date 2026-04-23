def _find_record(
            self, xmlid=None, res_model='ir.attachment', res_id=None,
            access_token=None, field=None
    ):
        """
        Find and return a record either using an xmlid either a model+id
        pair. This method is an helper for the ``/web/content`` and
        ``/web/image`` controllers and should not be used in other
        contextes.

        :param Optional[str] xmlid: xmlid of the record
        :param Optional[str] res_model: model of the record,
            ir.attachment by default.
        :param Optional[id] res_id: id of the record
        :param Optional[str] access_token: access token to use instead
            of the access rights and access rules.
        :param Optional[str] field: image field name to check the access to
        :returns: single record
        :raises MissingError: when no record was found.
        """
        record = None
        if xmlid:
            record = self.env.ref(xmlid, False)
        elif res_id is not None and res_model in self.env:
            record = self.env[res_model].browse(res_id).exists()
        if not record:
            raise MissingError(f"No record found for xmlid={xmlid}, res_model={res_model}, id={res_id}")  # pylint: disable=missing-gettext
        if access_token and verify_limited_field_access_token(record, field, access_token, scope="binary"):
            return record.sudo()
        if record._can_return_content(field, access_token):
            return record.sudo()
        record.check_access("read")
        return record