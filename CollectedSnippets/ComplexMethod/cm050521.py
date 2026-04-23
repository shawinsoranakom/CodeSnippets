def setUpClass(cls):
        super().setUpClass()
        cls.env['project.share.wizard'].create({
            'res_model': 'project.project',
            'res_id': cls.project_portal.id,
            'collaborator_ids': [
                Command.create({'partner_id': cls.partner_portal.id, 'access_mode': 'edit'}),
            ],
        })

        Task = cls.env['project.task']
        readable_fields, writeable_fields = Task._portal_accessible_fields()

        # html_field_history is always silently ignored.
        field_exception = {"html_field_history"}

        cls.read_protected_fields_task = OrderedDict([
            (k, v)
            for k, v in Task._fields.items()
            if k in readable_fields and k not in field_exception
        ])
        cls.write_protected_fields_task = OrderedDict([
            (k, v)
            for k, v in Task._fields.items()
            if k in writeable_fields and k not in field_exception
        ])
        cls.readonly_protected_fields_task = OrderedDict([
            (k, v)
            for k, v in Task._fields.items()
            if k in readable_fields and k not in writeable_fields and k not in field_exception
        ])
        cls.other_fields_task = OrderedDict([
            (k, v)
            for k, v in Task._fields.items()
            if k not in readable_fields and k not in field_exception
        ])