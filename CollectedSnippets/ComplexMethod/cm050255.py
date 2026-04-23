def test_preferences_view_fields(self):
        """ A simple user should see all fields in preferences view, even if they are protected by groups """
        view = self.env.ref('hr.res_users_view_form_preferences')

        # For reference, check the view with user with every groups protecting user fields
        all_groups_xml_ids = chain(*[
            field.groups.split(',')
            for field in self.env['res.users']._fields.values()
            if field.groups
            if field.groups != '.' # "no-access" group on purpose
        ])
        all_groups = self.env['res.groups']
        for xml_id in all_groups_xml_ids:
            all_groups |= self.env.ref(xml_id.strip())
        user_all_groups = new_test_user(self.env, groups='base.group_user', login='hel', name='God')
        user_all_groups.write({'group_ids': [(4, group.id, False) for group in all_groups]})
        view_infos = self.env['res.users'].with_user(user_all_groups).get_view(view.id)
        full_fields = [el.get('name') for el in etree.fromstring(view_infos['arch']).xpath('//field[not(ancestor::field)]')]

        # Now check the view for a simple user
        user = new_test_user(self.env, login='gro', name='Grouillot')
        view_infos = self.env['res.users'].with_user(user).get_view(view.id)
        fields = [el.get('name') for el in etree.fromstring(view_infos['arch']).xpath('//field[not(ancestor::field)]')]

        # Compare both
        self.assertEqual(full_fields, fields, "View fields should not depend on user's groups")