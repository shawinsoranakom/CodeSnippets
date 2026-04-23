def _process_order(self, order, existing_order):
        """Create or update an pos.order from a given dictionary.

        :param dict order: dictionary representing the order.
        :param existing_order: order to be updated or False.
        :type existing_order: pos.order.
        :returns: id of created/updated pos.order
        :rtype: int
        """
        draft = True if order.get('state') == 'draft' else False
        pos_session = self.env['pos.session'].browse(order['session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            pos_session = self._get_valid_session(order)
            order['session_id'] = pos_session.id

        if not order.get('source'):
            order['source'] = 'pos'

        if order.get('partner_id'):
            partner_id = self.env['res.partner'].browse(order['partner_id'])
            if not partner_id.exists():
                order.update({
                    "partner_id": False,
                    "to_invoice": False,
                })

        if not order.get('company_id'):
            order['company_id'] = pos_session.config_id.company_id.id

        if self.env.context.get('current_order_uuid') and order['uuid'] == self.env.context['current_order_uuid']:
            # Prioritize the server date for the order that is currently being processed
            order['date_order'] = fields.Datetime.now()

        pos_order = False
        record_uuid_mapping = order.pop('relations_uuid_mapping', {})

        if not existing_order:
            pos_order = self.create({
                **{key: value for key, value in order.items() if key != 'name'},
            })
            pos_order = pos_order.with_company(pos_order.company_id)
        else:
            pos_order = existing_order

            # If the order is belonging to another session, it must be moved to the current session first
            if order.get('session_id') and order['session_id'] != pos_order.session_id.id:
                pos_order.write({'session_id': order['session_id']})

            # Save lines and payments before to avoid exception if a line is deleted
            # when vals change the state to 'paid'
            for field in ['lines', 'payment_ids']:
                if order.get(field):
                    existing_ids = set(pos_order[field].ids)
                    existing_line_ids = {line.uuid: line.id for line in pos_order[field]}
                    for line in order[field]:
                        if len(line) < 3:
                            continue
                        line_vals = line[2]
                        if line[0] == Command.CREATE and line_vals.get('uuid') in existing_line_ids:
                            # If we try to create (line[0] == Command.CREATE) a line with a uuid that already
                            # exists on another line of the same order, we transform the creation
                            # into an update (line[0] = Command.UPDATE) of the existing line.
                            line[0] = Command.UPDATE
                            line[1] = existing_line_ids[line_vals.get('uuid')]
                    pos_order.write({field: order[field]})
                    added_ids = set(pos_order[field].ids) - existing_ids
                    if added_ids:
                        _logger.info("Added %s %s to pos.order #%s", field, list(added_ids), pos_order.id)
                    order[field] = []

            del order['uuid']
            del order['access_token']
            if order.get('state') == 'paid':
                # The "paid" state will be assigned later by `_process_saved_order`
                order['state'] = pos_order.state
            pos_order.write(order)

        for model_name, mapping in record_uuid_mapping.items():
            owner_records = self.env[model_name].search([('uuid', 'in', mapping.keys())])
            for uuid, field_names in mapping.items():
                for name, uuids in field_names.items():
                    params = self.env[model_name]._fields[name]
                    if params.type in ['one2many', 'many2many']:
                        records = self.env[params.comodel_name].search([('uuid', 'in', uuids)])
                        owner_records.filtered(lambda r: r.uuid == uuid).write({name: [Command.link(r.id) for r in records]})
                    else:
                        record = self.env[params.comodel_name].search([('uuid', '=', uuids)])
                        owner_records.filtered(lambda r: r.uuid == uuid).write({name: record.id})

        self = self.with_company(pos_order.company_id)
        self._process_payment_lines(order, pos_order, pos_session, draft)
        return pos_order._process_saved_order(draft)