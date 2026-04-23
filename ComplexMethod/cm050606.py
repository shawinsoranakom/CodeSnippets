def _peppol_send_response(self, reference_moves, status, clarifications=None):
        self.ensure_one()
        clarifications = clarifications or []
        reference_moves = reference_moves.filtered(lambda rm: rm.peppol_message_uuid and rm.peppol_can_send_response)
        if not reference_moves:
            return

        assert status in {'AB', 'AP', 'RE'}
        if status == 'RE' and (
            not clarifications
            or not any(clarification['list_identifier'] == 'OPStatusReason' for clarification in clarifications)
        ):
            raise ValidationError(self.env._('At least one reason must be given when rejecting a Peppol invoice.'))

        try:
            response = self._call_peppol_proxy(
                "/api/peppol/1/send_response",
                params={
                    'reference_uuids': reference_moves.mapped('peppol_message_uuid'),
                    'status': status,
                    'clarifications': clarifications,
                },
            )
        except UserError as e:
            log_message = self.env._(
                "An error occurred while responding to this invoice's expeditor.%(br)sStatus: %(status)s - %(error)s",
                br=Markup('<br/>'),
                status=status,
                error=str(e),
            )
            reference_moves._message_log_batch(
                bodies={move.id: log_message for move in reference_moves},
            )
        else:
            self.env['account.peppol.response'].create([{
                    'peppol_message_uuid': message['message_uuid'],
                    'response_code': status,
                    'peppol_state': 'processing',
                    'move_id': move.id,
                }
                for message, move in zip(response.get('messages'), reference_moves)
            ])
            log_message = self.env._(
                "A Peppol response was sent to the Peppol Access Point declaring you %(status)s this document.",
                status=self.env._('received') if status == 'AB' else self.env._('accepted') if status == 'AP' else self.env._('rejected'),
            )
            reference_moves._message_log_batch(bodies={move.id: log_message for move in reference_moves})