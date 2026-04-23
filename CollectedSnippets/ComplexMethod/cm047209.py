def test_address_first_contact_sync(self):
        """ Test initial creation of company/contact pair where contact address gets copied to
        company """
        (
            void_parent_ct, void_parent_comp, full_parent_ct, full_parent_comp,
            void_parent_withparent, full_parent_withparent,
        ) = self.env['res.partner'].create([
            {  # contact parents
                'name': 'Void Ct',
                'is_company': False,
            }, {
                'name': 'Void Comp',
                'is_company': True,
            }, {  # company parents
                'name': 'Full Ct',
                'is_company': False,
                **self.test_address_values_2,
            }, {
                'name': 'Full Comp',
                'is_company': False,
                **self.test_address_values_2,
            }, {  # parent being itself a child of another partner
                'name': 'Void Ct With Parent',
                'parent_id': self.test_parent.id,
            }, {
                'name': 'Full Ct With Parent',
                'parent_id': self.test_parent.id,
                **self.test_address_values_2,
            },
        ])
        for parent in (void_parent_ct + void_parent_comp + full_parent_ct + full_parent_comp):
            with self.subTest(parent_name=parent.name):
                p1 = self.env['res.partner'].create(dict(
                    {
                    'name': 'Micheline Brutijus',
                    'parent_id': parent.id,
                    }, **self.test_address_values_3)
                )
                self.assertEqual(p1.type, 'contact', 'Default type must be "contact", not the copied parent type')
                if parent in (void_parent_ct, void_parent_comp):
                    for fname, fvalue in self.test_address_values_3_cmp.items():
                        self.assertEqual(p1[fname], fvalue, 'Creation value taken')
                        self.assertEqual(parent[fname], fvalue, 'Should sync void parent to first contact')
                elif parent in (full_parent_ct, full_parent_comp):
                    for fname, fvalue in self.test_address_values_2_cmp.items():
                        self.assertEqual(p1[fname], fvalue, 'Parent wins over creation values')
                        self.assertEqual(parent[fname], fvalue, 'Should not sync parent with address to first contact')
                elif parent == full_parent_withparent:
                    for fname, fvalue in self.test_address_values_cmp.items():
                        self.assertEqual(p1[fname], fvalue)
                        self.assertEqual(parent[fname], fvalue, 'Should not sync parent that is not root to first contact')
                elif parent == void_parent_withparent:
                    for fname, fvalue in self.test_address_values_cmp.items():
                        self.assertEqual(p1[fname], fvalue)
                        self.assertFalse(parent[fname], 'Should not sync parent that is not root to first contact, event when void')