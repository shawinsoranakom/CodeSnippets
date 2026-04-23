def test_address(self):
        # check initial data
        for fname, fvalue in self.test_address_values_cmp.items():
            self.assertEqual(self.existing[fname], fvalue)

        # future new child
        ct1 = self.env['res.partner'].browse(
            self.env['res.partner'].name_create('Denis Bladesmith <denis.bladesmith@ghoststep.com>')[0]
        )
        self.assertEqual(ct1.type, 'contact', 'Default type must be "contact"')

        ct2, inv, deli, other = self.env['res.partner'].create([
            {
                'name': 'Address, Future Sibling of P1',
                **self.test_address_values_3,
            }, {
                'name': 'Invoice Child',
                'street': 'Invoice Child Street',
                'type': 'invoice',
            }, {
                'name': 'Delivery Child',
                'street': 'Delivery Child Street',
                'type': 'delivery',
            }, {
                'name': 'Other Child',
                'street': 'Other Child Street',
                'type': 'other',
            },
        ])
        ct1_1, inv_1 = self.env['res.partner'].create([
            {
                'name': 'Address, Child of P1',
                'parent_id': ct1.id,
            }, {
                'name': 'Address, Child of Invoice',
                'parent_id': inv.id,
            },
        ])
        # check creation values
        for fname in self.base_address_fields:
            self.assertFalse(ct1_1[fname])
        self.assertFalse(ct1_1.vat)
        self.assertEqual(inv_1.street, 'Invoice Child Street', 'Should take parent address')
        self.assertFalse(inv_1.vat)
        # test it also works with default_parent_id value in context
        # also ensure it works directly on a non-empty recordset
        inv_2 = (ct1_1 | inv_1).with_context(default_parent_id=inv.id).create({
            'name': 'Address, Child of Invoice',
        })
        self.assertEqual(inv_2.street, 'Invoice Child Street', 'Should take parent address')
        self.assertFalse(inv_2.vat)

        # sync P1 with parent, check address is update + other fields in write kept
        ct1_phone = '+320455999999'
        ct1.write({
            'phone': ct1_phone,
            'parent_id': self.test_parent.id,
        })
        for fname, fvalue in self.test_address_values_cmp.items():
            self.assertEqual(ct1[fname], fvalue)
            # Note: update is done only for direct children of parent
            self.assertFalse(ct1_1[fname], 'Descendants are not updated, only direct children')
        self.assertEqual(ct1.email, 'denis.bladesmith@ghoststep.com', 'Email should be preserved after sync')
        self.assertEqual(ct1.phone, ct1_phone, 'Phone should be preserved after address sync')
        self.assertEqual(ct1.type, 'contact', 'Type should be preserved after address sync')
        self.assertEqual(ct1.vat, 'BE0477472701', 'VAT should come from parent')
        self.assertEqual(ct1.industry_id, self.test_industries[0], 'Industry should come from parent')
        self.assertEqual(ct1.company_registry, '0477472701', 'Company registry should come from parent')

        # turn off sync: do what you want
        ct1_street = 'Different street, 42'
        ct1.write({
            'street': ct1_street,
            'state_id': False,
            'type': 'invoice',
        })
        self.assertEqual(ct1.street, ct1_street, 'Address fields must not be synced after turning sync off')
        self.assertEqual(ct1.zip, '1367', 'Address fields not changed in write should have kept their value')
        for fname in self.base_address_fields:
            # Note: only updated values are sync
            if fname == 'street':
                self.assertEqual(ct1_1[fname], ct1_street)
            else:
                self.assertFalse(ct1_1[fname])
        self.assertEqual(ct1.type, 'invoice')
        self.assertEqual(ct1.parent_id, self.test_parent, 'Changing address should not break hierarchy')
        self.assertNotEqual(self.test_parent.street, ct1_street, 'Parent address must not be touched')

        # turn on sync again: should reset address to parent
        ct1.write({'type': 'contact'})
        for fname, fvalue in self.test_address_values_cmp.items():
            self.assertEqual(ct1[fname], fvalue)
            # Note: update is done only for direct children of parent
            if fname == 'street':
                self.assertEqual(ct1_1[fname], ct1_street)
            else:
                self.assertFalse(ct1_1[fname])
        self.assertEqual(ct1.type, 'contact', 'Type should be preserved after address sync')

        # set P2 as sibling of P1 -> should update address
        ct2.write({'parent_id': self.test_parent.id})
        for fname, fvalue in self.test_address_values_cmp.items():
            self.assertEqual(ct2[fname], fvalue)

        # DOWNSTREAM: parent -> children
        # ------------------------------------------------------------
        self.test_parent.write(self.test_address_values_2)
        for fname, fvalue in self.test_address_values_2_cmp.items():
            self.assertEqual(ct1[fname], fvalue)
            self.assertEqual(ct2[fname], fvalue)
            self.assertEqual(self.existing[fname], fvalue)
        # but child of P3 is not updated, as only 1 level is updated
        for fname in self.base_address_fields:
            if fname == 'street':
                self.assertEqual(ct1_1[fname], ct1_street, 'Updated only through P1 direct update')
            else:
                self.assertFalse(ct1_1[fname], 'Still holding base creation values, no descendants update')
        # and not-contacts are not updated
        for child in inv, deli, other:
            self.assertEqual(child.street, f'{child.name} Street', 'Should not be updated')

        # UPSTREAM: child -> parent update: contact update company
        # ------------------------------------------------------------
        ct1.write(self.test_address_values_3)
        for fname, fvalue in self.test_address_values_3_cmp.items():
            self.assertEqual(self.test_parent[fname], fvalue)
            self.assertEqual(ct1[fname], fvalue)
            self.assertEqual(ct1_1[fname], fvalue)
            self.assertEqual(ct2[fname], fvalue)