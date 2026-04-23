def handle_history_divergence(record, html_field_name, vals):
    # Do not handle history divergence if the field is not in the values.
    if html_field_name not in vals:
        return
    # Do not handle history divergence if in module installation mode.
    if record.env.context.get('install_module'):
        return
    incoming_html = vals[html_field_name]
    incoming_history_matches = re.search(diverging_history_regex, incoming_html or '')
    # When there is no incoming history id, it means that the value does not
    # comes from the odoo editor or the collaboration was not activated. In
    # project, it could come from the collaboration pad. In that case, we do not
    # handle history divergences.
    if request:
        channel = (request.db, 'editor_collaboration', record._name, html_field_name, record.id)
    if incoming_history_matches is None:
        if request:
            bus_data = {
                'model_name': record._name,
                'field_name': html_field_name,
                'res_id': record.id,
                'notificationName': 'html_field_write',
                'notificationPayload': {'last_step_id': None},
            }
            request.env['bus.bus']._sendone(channel, 'editor_collaboration', bus_data)
        return
    incoming_history_ids = incoming_history_matches[1].split(',')
    last_step_id = incoming_history_ids[-1]

    bus_data = {
        'model_name': record._name,
        'field_name': html_field_name,
        'res_id': record.id,
        'notificationName': 'html_field_write',
        'notificationPayload': {'last_step_id': last_step_id},
    }
    if request:
        request.env['bus.bus']._sendone(channel, 'editor_collaboration', bus_data)

    if record[html_field_name]:
        server_history_matches = re.search(diverging_history_regex, record[html_field_name] or '')
        # Do not check old documents without data-last-history-steps.
        if server_history_matches:
            server_last_history_id = server_history_matches[1].split(',')[-1]
            if server_last_history_id not in incoming_history_ids:
                logger.warning('The document was already saved from someone with a different history for model %r, field %r with id %r.', record._name, html_field_name, record.id)
                raise ValidationError(_(
                    'The document was already saved from someone with a different history for model "%(model)s", field "%(field)s" with id "%(id)d".',
                    model=record._name,
                    field=html_field_name,
                    id=record.id,
                ))

    # Save only the latest id.
    vals[html_field_name] = incoming_html[0:incoming_history_matches.start(1)] + last_step_id + incoming_html[incoming_history_matches.end(1):]