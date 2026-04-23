def test_commercial_field_sync(self):
        """Check if commercial fields are synced properly: testing with VAT field"""
        company_1, company_2 = self.env['res.partner'].create([
            {
                'company_registry': '123456789',
                'industry_id': self.test_industries[0].id,
                'is_company': True,
                'name': 'company 1',
                'vat': 'BE013456789',
            }, {
                'company_registry': '9876543210',
                'industry_id': self.test_industries[0].id,
                'is_company': True,
                'name': 'company 2',
                'vat': 'BE9876543210',
            },
        ])

        contact = self.env['res.partner'].create({'name': 'someone', 'is_company': False, 'parent_id': company_1.id})
        self.assertEqual(contact.commercial_partner_id, company_1, "Commercial partner should be recomputed")
        for fname in ('company_registry', 'industry_id', 'vat'):
            self.assertEqual(contact[fname], company_1[fname], "Commercial field should be inherited from the company 1")

        # create a delivery address and a child for the partner
        contact_dlr = self.env['res.partner'].create({'name': 'somewhere', 'type': 'delivery', 'parent_id': contact.id})
        self.assertEqual(contact_dlr.commercial_partner_id, company_1, "Commercial partner should be recomputed")
        for fname in ('company_registry', 'industry_id', 'vat'):
            self.assertEqual(contact_dlr[fname], company_1[fname], "Commercial field should be inherited from the company 1")
        contact_ct = self.env['res.partner'].create({'name': 'child someone', 'parent_id': contact.id})
        self.assertEqual(contact_dlr.commercial_partner_id, company_1, "Commercial partner should be recomputed")
        for fname in ('company_registry', 'industry_id', 'vat'):
            self.assertEqual(contact_dlr[fname], company_1[fname], "Commercial field should be inherited from the company 1")

        # move the partner to another company
        contact.write({'parent_id': company_2.id})
        self.assertEqual(contact.commercial_partner_id, company_2, "Commercial partner should be recomputed")
        for fname in ('company_registry', 'industry_id', 'vat'):
            self.assertEqual(contact[fname], company_2[fname], "Commercial field should be inherited from the company 2")
        self.assertEqual(contact_dlr.commercial_partner_id, company_2, "Commercial partner should be recomputed on delivery")
        for fname in ('company_registry', 'industry_id', 'vat'):
            self.assertEqual(contact_dlr[fname], company_2[fname], "Commecial field should be inherited from the company 2 to delivery")
        self.assertEqual(contact_ct.commercial_partner_id, company_2, "Commercial partner should be recomputed on delivery")
        for fname in ('company_registry', 'industry_id', 'vat'):
            self.assertEqual(contact_ct[fname], company_2[fname], "Commecial field should be inherited from the company 2 to delivery")

        # check using embedded 2many commands
        company_2.write({'child_ids': [(0, 0, {'name': 'Alrik Greenthorn', 'email': 'agr@sunhelm.com'})]})
        contact2 = self.env['res.partner'].search([('email', '=', 'agr@sunhelm.com')])
        for fname in ('company_registry', 'industry_id', 'vat'):
            self.assertEqual(contact2[fname], company_2[fname], "Commercial field should be inherited from the company 2")

        # DOWNSTREAM update to descendants
        company_2.write({'company_registry': 'new', 'industry_id': self.test_industries[1].id, 'vat': 'BEnew'})
        for partner in contact + contact_dlr + contact_ct + contact2:
            for fname, fvalue in (('company_registry', 'new'), ('industry_id', self.test_industries[1]), ('vat', 'BEnew')):
                self.assertEqual(partner[fname], fvalue, "Commercial field should be updated from the company 2")

        # UPSTREAM: now supported
        contactvat = 'BE445566'
        contact.write({'vat': contactvat})
        for partner in company_2 + contact + contact_dlr + contact_ct + contact2:
            self.assertEqual(partner.vat, contactvat, 'Commercial sync works upstream, therefore also for siblings')

        # MISC PARENT MANIPULATION
        # promote p1 to commercial entity
        newcontactvat = 'BE998877'
        contact.write({
            'parent_id': company_1.id,
            'is_company': True,
            'name': 'Sunhelm Subsidiary',
            'vat': newcontactvat,
        })
        self.assertEqual(contact.vat, newcontactvat, 'Setting is_company should stop auto-sync of commercial fields')
        self.assertEqual(contact.commercial_partner_id, contact, 'Incorrect commercial entity resolution after setting is_company')
        self.assertEqual(contact2.vat, contactvat, 'Old sibling untouched')
        self.assertEqual(company_1.vat, 'BE013456789', 'Should not impact parent')
        self.assertEqual(contact_dlr.vat, newcontactvat, 'Promotion propagated')
        self.assertEqual(contact_ct.vat, newcontactvat, 'Promotion propagated')

        # change parent of commercial entity
        contact.write({'parent_id': company_2.id})
        self.assertEqual(contact.vat, newcontactvat, 'Setting is_company should stop auto-sync of commercial fields')
        self.assertEqual(contact.commercial_partner_id, contact, 'Incorrect commercial entity resolution after setting is_company')
        self.assertEqual(company_2.vat, contactvat, 'Should not impact parent')
        self.assertEqual(contact_dlr.vat, newcontactvat, 'Parent company stop auto sync')
        self.assertEqual(contact_ct.vat, newcontactvat, 'Parent company stop auto sync')

        # writing on parent should not touch child commercial entities
        sunhelmvat2 = 'BE0112233453'
        company_2.write({'vat': sunhelmvat2})
        for partner in contact + contact_ct + contact_dlr:
            self.assertEqual(contact.vat, newcontactvat, 'Setting is_company should stop auto-sync of commercial fields')
        for partner in contact2:
            self.assertEqual(partner.vat, sunhelmvat2, 'Commercial fields must be automatically synced')