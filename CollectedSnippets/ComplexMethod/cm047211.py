def test_06_fields(self):
        """ Check that relation fields return records, recordsets or nulls. """
        user = self.env.user
        self.assertIsRecord(user, 'res.users')
        self.assertIsRecord(user.partner_id, 'res.partner')
        self.assertIsRecordset(user.group_ids, 'res.groups')

        for name, field in self.partners._fields.items():
            if field.type == 'many2one':
                for p in self.partners:
                    self.assertIsRecord(p[name], field.comodel_name)
            elif field.type == 'reference':
                for p in self.partners:
                    if p[name]:
                        self.assertIsRecord(p[name], field.comodel_name)
            elif field.type in ('one2many', 'many2many'):
                for p in self.partners:
                    self.assertIsRecordset(p[name], field.comodel_name)