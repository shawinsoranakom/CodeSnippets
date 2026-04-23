def _fetch_attachment(self):
        """
        This method will check if we have any existent attachement matching the model
        and res_ids and create them if not found.
        """
        self.ensure_one()
        if not self.attachment_id:
            report = self.report_template
            if not report:
                report_name = self.env.context.get('report_name')
                report = self.env['ir.actions.report']._get_report_from_name(report_name)
                if not report:
                    return False
                else:
                    self.write({'report_template': report.id})
            paperformat = report.get_paperformat()
            if (paperformat.format == 'custom' and paperformat.page_width != 210 and paperformat.page_height != 297) or paperformat.format != 'A4':
                raise UserError(_("Please use an A4 Paper format."))
            # The external_report_layout_id is changed just for the snailmail pdf generation if the layout is not supported
            prev = self.company_id.external_report_layout_id
            if prev in {
                self.env.ref(f'web.external_layout_{layout}')
                for layout in ('bubble', 'wave', 'folder')
            }:
                self.company_id.sudo().external_report_layout_id = self.env.ref('web.external_layout_standard')
            filename, pdf_bin = self._generate_report_pdf(report)
            self.company_id.sudo().external_report_layout_id = prev

            pdf_bin = self._overwrite_margins(pdf_bin)
            if self.cover:
                pdf_bin = self._append_cover_page(pdf_bin)
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'datas': base64.b64encode(pdf_bin),
                'res_model': 'snailmail.letter',
                'res_id': self.id,
                'type': 'binary',  # override default_type from context, possibly meant for another model!
            })
            self.write({'attachment_id': attachment.id})

        return self.attachment_id