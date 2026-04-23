def _extend_with_attachments(self, files_data, new=False):
        """ Extend/enhance a business document with one or more attachments.

        Only the attachment with the highest priority will be used to extend the business document,
        using the appropriate decoder.

        The decoder may break Python and SQL constraints in difficult-to-predict ways.
        This method calls the decoder in such a way that any exceptions instead roll back the transaction
        and log a message on the invoice chatter.

        This method will not extract embedded files for you - if you want embedded files to be
        considered, you must pass them as part of the `attachments` recordset.

        :param self:        An invoice on which to apply the attachments.
        :param files_data:  A list of file_data dicts, each representing an in-DB or extracted attachment.
        :param new:         If true, indicates that the invoice was newly created, will be passed to the decoder.
        :return:            True if at least one document is successfully imported.

        ⚠️ Because this method commits the cursor, try to:
        (1) do as much work as possible before calling this method, and
        (2) avoid triggering a SerializationError later in the request. If a SerializationError happens,
            `retrying` will cause the whole request to be retried, which may cause some things
            to be duplicated. That may be more or less undesirable, depending on what you're doing.
        """
        def _get_attachment_name(file_data):
            params = {
                'filename': file_data['name'],
                'root_filename': file_data['origin_attachment'].name,
                'type': file_data['import_file_type'],
            }
            if not file_data['attachment']:
                return self.env._("'%(filename)s' (extracted from '%(root_filename)s', type=%(type)s)", **params)
            else:
                return self.env._("'%(filename)s' (type=%(type)s)", **params)

        self.ensure_one()

        for file_data in files_data:
            if 'decoder_info' not in file_data:
                file_data['decoder_info'] = self._get_edi_decoder(file_data, new=new)

        # Identify the attachment to decode.
        sorted_files_data = sorted(
            files_data,
            key=lambda file_data: (
                file_data['decoder_info'] is not None,
                (file_data['decoder_info'] or {}).get('priority', 0),
            ),
            reverse=True,
        )

        file_data = sorted_files_data[0]

        if file_data['decoder_info'] is None or file_data['decoder_info'].get('priority', 0) == 0:
            _logger.info(
                "Attachment(s) %s not imported: no suitable decoder found.",
                [file_data['name'] for file_data in files_data],
            )
            return

        try:
            with rollbackable_transaction(self.env.cr):
                reason_cannot_decode = file_data['decoder_info']['decoder'](self, file_data, new)
                if reason_cannot_decode:
                    self.message_post(
                        body=self.env._(
                            "Attachment %(filename)s not imported: %(reason)s",
                            filename=file_data['name'],
                            reason=reason_cannot_decode,
                        )
                    )
                    return
        except RedirectWarning:
            raise
        except Exception as e:
            _logger.exception("Error importing attachment %s on record %s", file_data['name'], self)

            self.sudo().message_post(body=Markup("%s<br/><br/>%s<br/>%s") % (
                self.env._(
                    "Error importing attachment %(filename)s:",
                    filename=_get_attachment_name(file_data),
                ),
                self.env._("This specific error occurred during the import:"),
                str(e),
            ))
            return
        return True