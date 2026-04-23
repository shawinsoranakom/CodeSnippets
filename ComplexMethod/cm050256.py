def setUpClass(cls):
        super(TestSelfAccessRights, cls).setUpClass()
        cls.richard = new_test_user(cls.env, login='ric', groups='base.group_user', name='Simple employee', email='ric@example.com')
        cls.richard_emp = cls.env['hr.employee'].create({
            'name': 'Richard',
            'user_id': cls.richard.id,
            'private_phone': '21454',
        })
        cls.hubert = new_test_user(cls.env, login='hub', groups='base.group_user', name='Simple employee', email='hub@example.com')
        cls.hubert_emp = cls.env['hr.employee'].create({
            'name': 'Hubert',
            'user_id': cls.hubert.id,
        })

        cls.protected_fields_emp = OrderedDict([(k, v) for k, v in cls.env['hr.employee']._fields.items() if v.groups == 'hr.group_hr_user'])
        # Compute fields and id field are always readable by everyone
        cls.read_protected_fields_emp = OrderedDict([(k, v) for k, v in cls.env['hr.employee']._fields.items() if not v.compute and k != 'id'])
        cls.self_protected_fields_user = OrderedDict([
            (k, v)
            for k, v in cls.env['res.users']._fields.items()
            if v.groups == 'hr.group_hr_user' and k in cls.env['res.users'].SELF_READABLE_FIELDS
        ])