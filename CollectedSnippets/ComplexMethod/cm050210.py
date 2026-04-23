def setUpClass(cls):
        super().setUpClass()

        cls.records_access = cls.env['mail.test.access'].create([
            {'name': 'Access.1', 'access': 'public'},
            {'name': 'Access.2', 'access': 'logged'},
            {'name': 'Access.3', 'access': 'followers'},
        ])
        cls.records_access_custo = cls.env['mail.test.access.custo'].create([
            {'name': 'Custo.1'},
            {'name': 'Custo.2', 'is_readonly': True},  # read access, should be able to read messages / activities
            {'name': 'Custo.3', 'is_locked': True},  # not able to read messages / activities
        ])
        cls.records_mc = cls.env['mail.test.multi.company'].create([
            {'name': 'MC.1'},
            {'name': 'MC.2'},
            {'name': 'MC.3'},
        ])

        # messages to check access
        cls.messages = cls.env['mail.message']
        for records_model in [cls.records_access, cls.records_access_custo, cls.records_mc]:
            for record in records_model:
                cls.messages += record.with_user(cls.user_admin).message_post(
                    body=f'Posting on {record.name}',
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
        # message employee cannot read due to specific rules (aka locked record)
        cls.messages_emp_nope = cls.messages[5]

        # activities to check access
        cls.activities = cls.env['mail.activity']
        for records_model in [cls.records_access, cls.records_access_custo, cls.records_mc]:
            cls.activities += cls.env['mail.activity'].create([
                {
                    'res_id': record.id,
                    'res_model_id': cls.env['ir.model']._get_id(record._name),
                    'summary': f'TestActivity {idx} on {record._name},{record.id} for {user.name}',
                    'user_id': user.id,
                }
                for record in records_model
                for user in (cls.user_admin + cls.user_employee)
                for idx in range(2)
            ])
            records_model.message_unsubscribe(partner_ids=(cls.user_admin + cls.user_employee).partner_id.ids)
        # activities employee cannot read due to specific rules (other user on non open custo)
        cls.activities_emp_nope = cls.activities.filtered(
            lambda a: a.res_model == 'mail.test.access.custo' and a.res_id == cls.records_access_custo[2].id and a.user_id == cls.user_admin
        )