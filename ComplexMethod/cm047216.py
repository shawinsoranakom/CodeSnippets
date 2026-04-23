def test_res_groups_fullname_search(self):
        monkey = self.env['res.groups.privilege'].create({'name': 'Monkey'})
        self.env['res.groups']._load_records([{
            'xml_id': 'base.test_monkey_banana',
            'values': {'name': 'Banana', 'privilege_id': monkey.id},
        }, {
            'xml_id': 'base.test_monkey_stuff',
            'values': {'name': 'Stuff', 'privilege_id': monkey.id},
        }, {
            'xml_id': 'base.test_monkey_administrator',
            'values': {'name': 'Administrator', 'privilege_id': monkey.id},
        }, {
            'xml_id': 'base.test_donky',
            'values': {'name': 'Donky Monkey'},
        }])

        all_groups = self.env['res.groups'].search([])

        groups = all_groups.search([('full_name', 'like', 'Sale')])
        self.assertItemsEqual(groups.ids, [g.id for g in all_groups if 'Sale' in g.full_name],
                              "did not match search for 'Sale'")

        groups = all_groups.search([('full_name', 'like', 'Master Data')])
        self.assertItemsEqual(groups.ids, [g.id for g in all_groups if 'Master Data' in g.full_name],
                              "did not match search for 'Master Data'")

        groups = all_groups.search([('full_name', 'like', 'Monkey/Banana')])
        self.assertItemsEqual(groups.mapped('full_name'), ['Monkey / Banana'],
                              "did not match search for 'Monkey/Banana'")

        groups = all_groups.search([('full_name', 'like', 'Monkey /')])
        self.assertItemsEqual(groups.ids, [g.id for g in all_groups if 'Monkey /' in g.full_name],
                              "did not match search for 'Monkey /'")

        groups = all_groups.search([('full_name', 'like', 'Monk /')])
        self.assertItemsEqual(groups.ids, [g.id for g in all_groups if 'Monkey /' in g.full_name],
                              "did not match search for 'Monk /'")

        groups = all_groups.search([('full_name', 'like', 'Monk')])
        self.assertItemsEqual(groups.ids, [g.id for g in all_groups if 'Monk' in g.full_name],
                              "did not match search for 'Monk'")

        groups = all_groups.search([('full_name', 'in', ['Creation'])])
        self.assertItemsEqual(groups.mapped('full_name'), ['Contact / Creation'])

        groups = all_groups.search([('full_name', 'in', ['Role / Administrator', 'Creation'])])
        self.assertItemsEqual(groups.mapped('full_name'), ['Contact / Creation', 'Role / Administrator'])

        groups = all_groups.search([('full_name', 'like', 'Admin')])
        self.assertItemsEqual(groups.mapped('full_name'), [g.full_name for g in all_groups if 'Admin' in g.full_name])

        groups = all_groups.search([('full_name', 'not like', 'Role /')])
        self.assertItemsEqual(groups.mapped('full_name'), [g.full_name for g in all_groups if 'Role /' not in g.full_name])

        groups = all_groups.search([('full_name', '=', False)])
        self.assertFalse(groups)

        groups = all_groups.search([('full_name', '!=', False)])
        self.assertEqual(groups, all_groups)

        groups = all_groups.search([('full_name', 'like', '/')])
        self.assertTrue(groups, "did not match search for '/'")