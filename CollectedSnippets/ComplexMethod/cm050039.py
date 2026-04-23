def setUpClass(cls):
        super().setUpClass()
        cls.test_users = cls.user_employee + cls.user_emp_inbox + cls.user_emp_email + cls.user_follower_emp_email + cls.user_follower_portal

        # rating-enabled test records
        with cls.mock_push_to_end_point(cls):
            cls.record_ratings = cls.env['mail.test.rating'].create([
                {
                    'customer_id': cls.customers[idx].id,
                    'name': f'TestRating_{idx}',
                    'user_id': cls.test_users[idx].id,

                }
                for idx in range(5)
            ])

        # messages and ratings
        user_id_field = cls.env['ir.model.fields']._get(cls.record_ratings._name, 'user_id')
        comment_subtype_id = cls.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
        cls.link_previews = cls.env["mail.link.preview"].create(
            [
                {"source_url": "https://www.odoo.com"},
                {"source_url": "https://www.example.com"},
            ]
        )
        cls.messages_all = cls.env['mail.message'].sudo().create([
            {
                'attachment_ids': [
                    (0, 0, {
                        'datas': 'data',
                        'name': f'Test file {att_idx}',
                        'res_id': record.id,
                        'res_model': record._name,
                    })
                    for att_idx in range(2)
                ],
                'author_id': record.customer_id.id,
                'body': f'<p>Test {msg_idx}</p>',
                'date': datetime(2023, 5, 15, 10, 30, 5),
                'email_from': record.customer_id.email_formatted,
                "message_link_preview_ids": [
                    Command.create({"link_preview_id": cls.link_previews[0].id}),
                    Command.create({"link_preview_id": cls.link_previews[1].id}),
                ],
                'notification_ids': [
                    (0, 0, {
                        'is_read': False,
                        'notification_type': 'inbox',
                        'res_partner_id': cls.customers[(msg_idx * 2)].id,
                    }),
                    (0, 0, {
                        'is_read': True,
                        'notification_type': 'email',
                        'notification_status': 'sent',
                        'res_partner_id': cls.customers[(msg_idx * 2) + 1].id,
                    }),
                ],
                'message_type': 'comment',
                'model': record._name,
                'partner_ids': [
                    (4, cls.customers[(msg_idx * 2)].id),
                    (4, cls.customers[record_idx].id),
                ],
                'reaction_ids': [
                    (0, 0, {
                        'content': 'https://www.odoo.com',
                        'partner_id': cls.customers[(msg_idx * 2) + 1].id
                    }), (0, 0, {
                        'content': 'https://www.example.com',
                        'partner_id': cls.customers[record_idx].id
                    }),
                ],
                'res_id': record.id,
                'subject': f'Test Rating {msg_idx}',
                'subtype_id': comment_subtype_id,
                'starred_partner_ids': [
                    (4, cls.customers[(msg_idx * 2)].id),
                    (4, cls.customers[(msg_idx * 2) + 1].id),
                ],
                'tracking_value_ids': [
                    (0, 0, {
                        'field_id': user_id_field.id,
                        'new_value_char': 'new 1',
                        'new_value_integer': record.user_id.id,
                        'old_value_char': 'old 1',
                        'old_value_integer': cls.user_admin.id,
                    }),
                ]
            }
            for msg_idx in range(2)
            for record_idx, record in enumerate(cls.record_ratings)
        ])

        cls.messages_records = [cls.env[message.model].browse(message.res_id) for message in cls.messages_all]
        # ratings values related to rating-enabled records
        cls.ratings_all = cls.env['rating.rating'].sudo().create([
            {
                'consumed': True,
                'message_id': message.id,
                'partner_id': record.customer_id.id,
                'publisher_comment': 'Comment',
                'publisher_id': cls.user_admin.partner_id.id,
                'publisher_datetime': datetime(2023, 5, 15, 10, 30, 5) - timedelta(days=2),
                'rated_partner_id': record.user_id.partner_id.id,
                'rating': 4,
                'res_id': message.res_id,
                'res_model_id': cls.env['ir.model']._get_id(message.model),
            }
            for rating_idx in range(2)
            for message, record in zip(cls.messages_all, cls.messages_records)
        ])