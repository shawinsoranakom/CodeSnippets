def _process_attendees_form(self, event, form_details):
        """ Process data posted from the attendee details form.
        Extracts question answers:
        - For both questions asked 'once_per_order' and questions asked to every attendee
        - For questions of type 'simple_choice', extracting the suggested answer id
        - For questions of type 'text_box', extracting the text answer of the attendee.

        :param form_details: posted data from frontend registration form, like
            {'1-name': 'r', '1-email': 'r@r.com', '1-phone': '', '1-event_slot_id': '1', '1-event_ticket_id': '1'}
        """
        allowed_fields = request.env['event.registration']._get_website_registration_allowed_fields()
        registration_fields = {key: v for key, v in request.env['event.registration']._fields.items() if key in allowed_fields}
        for ticket_id in list(filter(lambda x: x is not None, [form_details[field] if 'event_ticket_id' in field else None for field in form_details.keys()])):
            if int(ticket_id) not in event.event_ticket_ids.ids and len(event.event_ticket_ids.ids) > 0:
                raise UserError(_("This ticket is not available for sale for this event"))
        registrations = {}
        general_answer_ids = []
        general_identification_answers = {}
        # as we may have several questions populating the same field (e.g: the phone)
        # we use this to hold the fields that have already been handled
        # goal is to use the answer to the first question of every 'type' (aka name / phone / email / company name)
        already_handled_fields_data = {}
        for key, value in form_details.items():
            if not value or '-' not in key:
                continue

            key_values = key.split('-')
            # Special case for handling event_ticket_id data that holds only 2 values
            if len(key_values) == 2:
                registration_index, field_name = key_values
                if field_name not in registration_fields:
                    continue
                # Only cast when needed, as it might crash here for custom inputs in overrides
                if isinstance(registration_fields[field_name], (fields.Many2one, fields.Integer)):
                    value = int(value) or False
                registrations.setdefault(registration_index, dict())[field_name] = value
                continue

            if len(key_values) != 3:
                continue

            registration_index, question_type, question_id = key_values
            answer_values = None
            if question_type == 'simple_choice':
                answer_values = {
                    'question_id': int(question_id),
                    'value_answer_id': int(value)
                }
            else:
                answer_values = {
                    'question_id': int(question_id),
                    'value_text_box': value
                }

            if answer_values and not int(registration_index):
                general_answer_ids.append((0, 0, answer_values))
            elif answer_values:
                registrations.setdefault(registration_index, dict())\
                    .setdefault('registration_answer_ids', list()).append((0, 0, answer_values))

            if question_type in ('name', 'email', 'phone', 'company_name')\
                and question_type not in already_handled_fields_data.get(registration_index, []):
                if question_type not in registration_fields:
                    continue

                field_name = question_type
                already_handled_fields_data.setdefault(registration_index, list()).append(field_name)

                if not int(registration_index):
                    general_identification_answers[field_name] = value
                else:
                    registrations.setdefault(registration_index, dict())[field_name] = value

        if general_answer_ids:
            for registration in registrations.values():
                registration.setdefault('registration_answer_ids', list()).extend(general_answer_ids)

        if general_identification_answers:
            for registration in registrations.values():
                registration.update(general_identification_answers)

        return list(registrations.values())