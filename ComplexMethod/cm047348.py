def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if not data:
            data = {}
        if isinstance(res_ids, int):
            res_ids = [res_ids]
        data.setdefault('report_type', 'pdf')

        collected_streams, report_type = self._pre_render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        if report_type != 'pdf':
            return collected_streams, report_type

        has_duplicated_ids = res_ids and len(res_ids) != len(set(res_ids))

        # access the report details with sudo() but keep evaluation context as current user
        report_sudo = self._get_report(report_ref)

        # Generate the ir.attachment if needed.
        if not has_duplicated_ids and report_sudo.attachment and not self.env.context.get("report_pdf_no_attachment"):
            attachment_vals_list = self._prepare_pdf_report_attachment_vals_list(report_sudo, collected_streams)
            if attachment_vals_list:
                attachment_names = ', '.join(x['name'] for x in attachment_vals_list)
                try:
                    self.env['ir.attachment'].create(attachment_vals_list)
                except AccessError:
                    _logger.info("Cannot save PDF report %r attachments for user %r", attachment_names, self.env.user.display_name)
                else:
                    _logger.info("The PDF documents %r are now saved in the database", attachment_names)

        def custom_handle_merge_pdfs_error(error, error_stream):
            error_record_ids.append(stream_to_ids[error_stream])

        stream_to_ids = {v['stream']: k for k, v in collected_streams.items() if v['stream']}
        # Merge all streams together for a single record.
        streams_to_merge = list(stream_to_ids.keys())
        error_record_ids = []

        if len(streams_to_merge) == 1:
            pdf_content = streams_to_merge[0].getvalue()
        else:
            with self._merge_pdfs(streams_to_merge, custom_handle_merge_pdfs_error) as pdf_merged_stream:
                pdf_content = pdf_merged_stream.getvalue()

        if error_record_ids:
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Problematic record(s)'),
                'res_model': report_sudo.model,
                'domain': [('id', 'in', error_record_ids)],
                'views': [(False, 'list'), (False, 'form')],
            }
            num_errors = len(error_record_ids)
            if num_errors == 1:
                action.update({
                    'views': [(False, 'form')],
                    'res_id': error_record_ids[0],
                })
            raise RedirectWarning(
                message=_('Odoo is unable to merge the generated PDFs because of %(num_errors)s corrupted file(s)', num_errors=num_errors),
                action=action,
                button_text=_('View Problematic Record(s)'),
            )

        for stream in streams_to_merge:
            stream.close()

        if res_ids:
            _logger.info("The PDF report has been generated for model: %s, records %s.", report_sudo.model, str(res_ids))

        return pdf_content, 'pdf'