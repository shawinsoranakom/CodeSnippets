def _nemhandel_send_response(self, reference_moves, status, note=False):
        self.ensure_one()
        reference_moves = reference_moves.filtered(lambda rm: rm.nemhandel_message_uuid and rm.partner_id.nemhandel_response_support)
        if not reference_moves:
            return

        assert status in {'BusinessAccept', 'BusinessReject'}

        try:
            response = self._call_nemhandel_proxy(
                "/api/nemhandel/1/send_response",
                params={
                    'reference_uuids': reference_moves.mapped('nemhandel_message_uuid'),
                    'status': status,
                    'note': note,
                },
            )
        except UserError as e:
            log_message = self.env._(
                "An error occurred with the Nemhandel proxy while responding to this invoice's expeditor.%(br)sResponse: %(status)s - %(error)s",
                br=Markup('<br>'),
                status=status,
                error=str(e),
            )
            reference_moves._message_log_batch(
                bodies={move.id: log_message for move in reference_moves},
            )
        else:
            if response.get('error'):
                log_message = self.env._(
                    "An error occurred with the Nemhandel server while responding to this invoice's expeditor.%(br)sStatus: %(status)s - %(error)s",
                    br=Markup('<br>'),
                    status=status,
                    error=response['error']['message'],
                )
                reference_moves._message_log_batch(
                    bodies={move.id: log_message for move in reference_moves},
                )
            else:
                self.env['nemhandel.response'].create([{
                        'nemhandel_message_uuid': message['message_uuid'],
                        'response_code': status,
                        'nemhandel_state': 'processing',
                        'move_id': move.id,
                    }
                    for message, move in zip(response.get('messages'), reference_moves)
                ])
                log_message = self.env._(
                    "A Nemhandel response was sent to the Nemhandel Access Point declaring you accepted this document.",
                ) if status == 'BusinessAccept' else self.env._(
                    "A Nemhandel response was sent to the Nemhandel Access Point declaring you rejected this document.",
                )
                reference_moves._message_log_batch(bodies={move.id: log_message for move in reference_moves})