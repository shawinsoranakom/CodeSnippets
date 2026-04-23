def _peppol_extract_response_info(self, document):
        doc_tree = etree.fromstring(document)
        blr_status = doc_tree.find('{*}DocumentResponse/{*}Response/{*}ResponseCode').text
        clarifications = self.env['account.peppol.clarification'].search([])
        clarification_messages = {'OPStatusReason': [], 'OPStatusAction': [], 'other': []}
        for status in doc_tree.findall('.//{*}Response/{*}Status'):
            status_reason_code = status.find('{*}StatusReasonCode')
            status_reason = status.find('{*}StatusReason')

            if status_reason_code is not None and status_reason is not None:
                # It is not mandatory in Peppol to have both (the reason code and the reason name/description) but at least one is required
                if status_reason_code.attrib['listID'] in {'OPStatusReason', 'OPStatusAction'}:
                    clarification_messages[status_reason_code.attrib['listID']].append(status_reason.text)
            elif status_reason_code is not None:
                if status_reason_code.attrib['listID'] in {'OPStatusReason', 'OPStatusAction'}:
                    clarification = clarifications.filtered(lambda c: c.list_identifier == status_reason_code.attrib['listID'] and c.code == status_reason_code.text)
                    clarification_messages[status_reason_code.attrib['listID']].append(clarification.name if clarification else status_reason_code.text)
            else:
                clarification = clarifications.filtered(lambda c: status_reason in (c.name, c.description))
                clarification_messages[clarification.list_identifier if clarification else 'other'].append(status_reason.text)

        rejection_message = ''
        if clarification_messages['OPStatusReason']:
            rejection_message = Markup('<b>{title}</b><br>{reasons}').format(
                title=self.env._("Reasons:"),
                reasons=format_list(self.env, clarification_messages['OPStatusReason']),
            )
        if clarification_messages['OPStatusAction']:
            rejection_message += (Markup('<br/>') if rejection_message else '') + Markup('<b>{title}</b><br>{actions}').format(
                title=self.env._("Suggested actions:"),
                actions=format_list(self.env, clarification_messages['OPStatusAction']),
            )
        if clarification_messages['other']:
            rejection_message += (Markup('<br/>') if rejection_message else '') + Markup('<b>{title}</b><br>{other}').format(
                title=self.env._('Miscellaneous:'),
                other=format_list(self.env, clarification_messages['other']),
            )

        return blr_status, rejection_message