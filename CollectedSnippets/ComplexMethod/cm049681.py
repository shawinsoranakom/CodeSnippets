def _l10n_sa_log_results(self, xml_content, response_data=None, error=False):
        """
            Save submitted invoice XML hash in case of either Rejection or Acceptance.
        """
        self.ensure_one()
        bootstrap_cls, title, subtitle, content = ("success", _("Success: Invoice accepted by ZATCA"), "", "" if (not error or not response_data) else response_data)
        status_code = response_data.get('status_code')
        attachment = False
        if error:
            xml_filename = self.env['account.edi.xml.ubl_21.zatca']._export_invoice_filename(self)
            xml_filename = xml_filename[:-4] + '-rejected.xml'
            attachment = self.env['ir.attachment'].create({
                'raw': xml_content,
                'name': xml_filename,
                'description': 'Rejected ZATCA Document not to be deleted - ثيقة ZATCA المرفوضة لا يجوز حذفها',
                'res_id': self.id,
                'res_model': self._name,
                'type': 'binary',
                'mimetype': 'application/xml',
            })
            bootstrap_cls, title = ("danger", _("Error: Invoice rejected by ZATCA"))
            subtitle = _('Please check the details below and retry after addressing them:')
            content = response_data['error']
        if response_data and response_data.get('validationResults', {}).get('warningMessages'):
            bootstrap_cls, title = ("warning", _("Warning: Invoice accepted by ZATCA with warnings"))
            subtitle = _('Please check the details below:')
            content = Markup("""<b>%(status_code)s</b>%(errors)s""") % {
                "status_code": f"[{status_code}] " if status_code else "",
                "errors": Markup("<br/>").join([
                    Markup("<b>%(code)s</b> : %(message)s") % {
                        "code": m['code'],
                        "message": m['message'],
                    } for m in response_data['validationResults']['warningMessages']
                ]),
            }
        if response_data.get("error") and response_data.get("excepted"):
            bootstrap_cls, title = ("warning", _("Warning: Unable to Retrieve a Response from ZATCA"))
            subtitle = _('Please check the details below:')
            content = response_data['error']
        if status_code == 409:
            bootstrap_cls, title = ("warning", _("Warning: Invoice was already successfully reported to ZATCA"))
            subtitle = _("Please check the details below:")
            content = Markup("""<b>%(status_code)s</b>%(errors)s""") % {
                "status_code": f"[{status_code}] " if status_code else "",
                "errors": Markup("<br/>").join([
                    Markup("<b>%(code)s</b> : %(message)s") % {
                        "code": m['code'],
                        "message": m['message'],
                    } for m in response_data['validationResults']['errorMessages']
                ])
            }
        if response_data.get("error") and not content:
            # if there is an error, but no exception or rejection in the response
            # then it is due to an internal error raised. No need to log a note
            return

        if not response_data.get("excepted"):
            self.journal_id.l10n_sa_latest_submission_hash = self.env['account.edi.xml.ubl_21.zatca']._l10n_sa_generate_invoice_xml_hash(xml_content)

        self.message_post(body=Markup("""
                <div role='alert' class='alert alert-%s'>
                    <h4 class='alert-heading my-0'>%s</h4>
                    <p class='mb-0 mt-1'>
                        %s
                    </p>
                    %s
                    <p class='mb-0'>
                        %s
                    </p>
                </div>
            """) % (bootstrap_cls, title, subtitle, Markup("<hr>") if content else "", content),
            attachment_ids=(attachment and [attachment.id]) or [],
        )