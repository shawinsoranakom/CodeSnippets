def _peppol_process_new_messages(self, messages):
        self.ensure_one()
        processed_uuids = []
        other_messages = {}
        origin_message_uuids = [content['origin_message_uuid'] for content in messages.values()]
        origin_moves = self.env['account.move'].search([
            ('peppol_message_uuid', 'in', origin_message_uuids),
            ('company_id', '=', self.company_id.id),
        ]).grouped('peppol_message_uuid')
        for uuid, content in messages.items():
            if content['document_type'] == 'ApplicationResponse':
                enc_key = content["enc_key"]
                document_content = content["document"]
                decoded_document = self._decrypt_data(document_content, enc_key)
                blr_status, rejection_message = self._peppol_extract_response_info(decoded_document)
                move = origin_moves.get(content['origin_message_uuid'])
                if move and blr_status in self.env['account.peppol.response']._fields['response_code']._selection:
                    self.env['account.peppol.response'].create({
                        'peppol_message_uuid': uuid,
                        'response_code': blr_status,
                        'peppol_state': content['state'],
                        'move_id': move.id,
                    })
                    # We only really support the AB, AP and RE codes for now,
                    # which are the only mandatory codes to support in order to correctly handle PEPPOL Business Responses.
                    # We still store the others.
                    if content['state'] == 'done':
                        if blr_status == 'RE':
                            move._message_log(
                                body=self.env._(
                                    "The Peppol receiver of this document has rejected it with the following information:%(br)s%(rejection_message)s",
                                    br=Markup("<br/>"),
                                    rejection_message=rejection_message,
                                )
                            )
                        elif blr_status in {'AB', 'AP'}:
                            move._message_log(
                                body=self.env._(
                                    "The Peppol receiver of this document replied that he has received it.",
                                ) if blr_status == 'AB' else self.env._(
                                    "The Peppol receiver of this document replied that he has accepted it.",
                                ),
                            )
                processed_uuids.append(uuid)
            else:
                other_messages[uuid] = content

        other_uuids, moves = super()._peppol_process_new_messages(other_messages)
        return processed_uuids + other_uuids, moves