def _peppol_process_messages_status(self, messages, uuid_to_record):
        self.ensure_one()
        processed_message_uuids = []
        other_messages = {}
        for uuid, content in messages.items():
            record = uuid_to_record[uuid]
            # In case of an error there is no 'document_type' in the content.
            if record._name != 'account.peppol.response' or 'document_type' in content and content['document_type'] != 'ApplicationResponse':
                other_messages[uuid] = content
                continue

            peppol_response = record
            if content.get('error'):
                if content['error'].get('code') == 702:
                    # "Peppol request not ready" error:
                    # thrown when the IAP is still processing the message
                    continue
                if content['error'].get('code') == 207:
                    peppol_response.peppol_state = 'not_serviced'
                else:
                    peppol_response.peppol_state = 'error'
                    peppol_response.move_id._message_log(
                        body=self.env._("Peppol business response error: %s", content['error'].get('data', {}).get('message') or content['error']['message']),
                    )
                processed_message_uuids.append(uuid)
                continue

            peppol_response.peppol_state = content['state']
            processed_message_uuids.append(uuid)
        return processed_message_uuids + super()._peppol_process_messages_status(other_messages, uuid_to_record)