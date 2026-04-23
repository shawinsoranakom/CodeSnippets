def _generate_template_attachments(self, res_ids, render_fields,
                                       render_results=None):
        """ Render attachments of template 'self', returning values for records
        given by 'res_ids'. Note that ``report_template_ids`` returns values for
        'attachments', as we have a list of tuple (report_name, base64 value)
        for those reports. It is considered as being the job of callers to
        transform those attachments into valid ``ir.attachment`` records.

        :param list res_ids: list of record IDs on which template is rendered;
        :param list render_fields: list of fields to render on template which
          are specific to attachments, e.g. attachment_ids or report_template_ids;
        :param dict render_results: res_ids-based dictionary of render values.
          For each res_id, a dict of values based on render_fields is given

        :return: updated (or new) render_results;
        """
        self.ensure_one()
        if render_results is None:
            render_results = {}

        # generating reports is done on a per-record basis, better ensure cache
        # is filled up to avoid rendering and browsing in a loop
        if res_ids and 'report_template_ids' in render_fields and self.report_template_ids:
            self.env[self.model].browse(res_ids)

        for res_id in res_ids:
            values = render_results.setdefault(res_id, {})

            # link template attachments directly
            if 'attachment_ids' in render_fields:
                values['attachment_ids'] = self.attachment_ids.ids

            # generate attachments (reports)
            if 'report_template_ids' in render_fields and self.report_template_ids:
                for report in self.report_template_ids:
                    # generate content
                    if report.report_type in ['qweb-html', 'qweb-pdf']:
                        report_content, report_format = self.env['ir.actions.report']._render_qweb_pdf(report, [res_id])
                    else:
                        render_res = self.env['ir.actions.report']._render(report, [res_id])
                        if not render_res:
                            raise UserError(_('Unsupported report type %s found.', report.report_type))
                        report_content, report_format = render_res
                    report_content = base64.b64encode(report_content)
                    # generate name
                    if report.print_report_name:
                        report_name = safe_eval(
                            report.print_report_name,
                            {
                                'object': self.env[self.model].browse(res_id),
                                'time': time,
                            }
                        )
                    else:
                        report_name = _('Report')
                    extension = "." + report_format
                    if not report_name.endswith(extension):
                        report_name += extension
                    values.setdefault('attachments', []).append((report_name, report_content))
            elif 'report_template_ids' in render_fields:
                values['attachments'] = []

        # hook for attachments-specific computation, used currently only for accounting
        if hasattr(self.env[self.model], '_process_attachments_for_template_post'):
            records_attachments = self.env[self.model].browse(res_ids)._process_attachments_for_template_post(self)
            for res_id, additional_attachments in records_attachments.items():
                if not additional_attachments:
                    continue
                if additional_attachments.get('attachment_ids'):
                    render_results[res_id].setdefault('attachment_ids', []).extend(additional_attachments['attachment_ids'])
                if additional_attachments.get('attachments'):
                    render_results[res_id].setdefault('attachments', []).extend(additional_attachments['attachments'])

        return render_results