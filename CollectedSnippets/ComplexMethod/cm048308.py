def _nemhandel_process_new_messages(self, messages):
        self.ensure_one()
        processed_uuids = []
        other_messages = {}
        origin_message_uuids = [content['origin_message_uuid'] for content in messages.values()]
        origin_moves = self.env['account.move'].search([
            ('nemhandel_message_uuid', 'in', origin_message_uuids),
            ('company_id', '=', self.company_id.id),
            ('partner_id', '!=', self.company_id.partner_id.id),
        ]).grouped('nemhandel_message_uuid')
        for uuid, content in messages.items():
            if content['document_type'] == 'ApplicationResponse':
                enc_key = content["enc_key"]
                document_content = content["document"]
                decoded_document = self._decrypt_data(document_content, enc_key)
                blr_status, note = self._nemhandel_extract_response_info(decoded_document)
                if move := origin_moves.get(content['origin_message_uuid']):
                    if blr_status in {'BusinessAccept', 'BusinessReject'}:
                        self.env['nemhandel.response'].create({
                            'nemhandel_message_uuid': uuid,
                            'response_code': blr_status,
                            'nemhandel_state': content['state'],
                            'move_id': move.id,
                        })
                        if content['state'] == 'done':
                            if blr_status == 'BusinessReject':
                                move._message_log(
                                    body=self.env._(
                                        "The Nemhandel receiver of this document has rejected it with the following information: %s",
                                        note
                                    ) if note else self.env._(
                                        "The Nemhandel receiver of this document has rejected it.",
                                    ),
                                )
                            else:
                                move._message_log(
                                    body=self.env._(
                                        "The Nemhandel receiver of this document has accepted it with the following information: %s",
                                        note,
                                    ) if note else self.env._(
                                        "The Nemhandel receiver of this document has accepted it.",
                                    ),
                                )
                    if blr_status in {'TechnicalReject', 'ProfileReject'}:
                        move._message_log(
                            body=self.env._(
                                "An issue arose with your Nemhandel document on the partner's side with the following information: %(note)s"
                                "%(br)sPlease contact the support if this issue persists.",
                                note=note,
                                br=Markup('<br>'),
                            ) if note else self.env._(
                                "An issue arose with your Nemhandel document on the partner's side."
                                "%(br)sPlease contact the support if this issue persists.",
                                br=Markup('<br>'),
                            ),
                        )
                processed_uuids.append(uuid)
            else:
                other_messages[uuid] = content

        other_uuids, moves = super()._nemhandel_process_new_messages(other_messages)
        return processed_uuids + other_uuids, moves