def l10n_hr_edi_mer_action_report_paid(self):
        batch = len(self) != 1
        for move in self:
            if not move.l10n_hr_mer_document_eid:
                continue
            state_to_set = {'partial': '3', 'paid': '2'}.get(move.payment_state)
            amount_to_report = (move.amount_total - move.amount_residual) - move.l10n_hr_payment_reported_amount
            if amount_to_report and state_to_set:
                try:
                    response = _mer_api_mark_paid(
                        move.company_id,
                        move.l10n_hr_mer_document_eid,
                        fields.Datetime.now(pytz.timezone('Europe/Zagreb')).strftime('%Y-%m-%dT%H:%M:%S'),
                        amount_to_report,
                        move.l10n_hr_payment_method_type,
                    )
                except MojEracunServiceError:
                    if batch:
                        _logger.error("Failed to report payments document: %s", move.l10n_hr_mer_document_eid)
                        continue
                    else:
                        raise
                move.l10n_hr_edi_addendum_id.payment_reported_amount += amount_to_report
                move.l10n_hr_edi_addendum_id.fiscalization_request = response.get('fiscalizationRequestId')
                if response.get('encodedXml'):
                    attachment = self.env["ir.attachment"].create(
                        {
                            "name": f"mojeracun_{response['electronicId']}_payment.xml",
                            "raw": response['encodedXml'],
                            "type": "binary",
                            "mimetype": "application/xml",
                        }
                    )
                    attachment.write({'res_model': 'account.move', 'res_id': move.id})
                else:
                    attachment = False
                move._message_log(
                    body=self.env._(
                        "%(ts)s: Payments for eRacun document (ElectroicId: %(eid)s) in the amount of %(mnt)s EUR has been reported successfully. (Request ID: %(req_id)s)",
                        ts=response['fiscalizationTimestamp'],
                        eid=move.l10n_hr_mer_document_eid,
                        mnt=amount_to_report,
                        req_id=response['fiscalizationRequestId'],
                    ),
                    attachment_ids=attachment.ids if attachment else False,
                )
                _mer_api_update_document_process_status(
                    move.company_id,
                    move.l10n_hr_mer_document_eid,
                    state_to_set,
                )
                move.l10n_hr_edi_addendum_id.business_document_status = state_to_set