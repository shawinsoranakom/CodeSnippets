def test_lead_convert_wizard_new_partner(self):
        no_partner = self.env['res.partner']
        test_partner_lead, test_partner_wizard, commercial_partner = self.env['res.partner'].create([
            {'name': 'Lead Test Partner'},
            {'name': 'Wizard Test Partner'},
            {'name': 'Company Partner', 'is_company': True},
        ])
        case_values = product(
            [no_partner, test_partner_lead],
            [False, 'New Company'],
            [no_partner, commercial_partner],
            [no_partner, test_partner_wizard],
            ['create', 'exist'],
        )
        for (lead_partner, lead_company_name, wizard_company, wizard_contact, wizard_action) in case_values:
            (test_partner_lead + test_partner_wizard).parent_id = False
            commercial_partner.invalidate_recordset()
            lead_contact_name = lead_partner.name or 'Test Contact Name'
            lead = self.env['crm.lead'].create({
                'name': 'Test Lead',
                'contact_name': lead_contact_name,
                'partner_id': lead_partner.id,
                'partner_name': lead_company_name,
            })
            wizard = self.env['crm.lead2opportunity.partner'].with_context({
                'active_model': 'crm.lead',
                'active_id': lead.id,
                'active_ids': lead.ids,
            }).create({})
            wizard.write({'action': wizard_action, 'name': 'convert'})
            if wizard_contact:
                wizard.partner_id = wizard_contact
            if wizard_company:
                wizard.commercial_partner_id = wizard_company
            with self.subTest(
                lead_company_name=lead_company_name, lead_partner=lead_partner.name,
                wizard_company=wizard_company.name, wizard_contact=wizard_contact.name, wizard_action=wizard_action
            ):
                wizard.action_apply()
                self.assertEqual(lead.type, 'opportunity')
                self.assertEqual(bool(lead.partner_id), bool(wizard_action == 'create' or lead_partner or wizard_contact))
                if wizard_action == 'exist' and (lead_partner or wizard_contact):
                    self.assertEqual(lead.partner_id, wizard_contact or lead_partner)
                if wizard_action == 'create' and not lead_partner and not wizard_contact and wizard_company:
                    self.assertTrue(lead.partner_id)
                    self.assertEqual(lead.partner_id.name, lead_contact_name)
                    self.assertEqual(lead.partner_id.parent_id, wizard_company)
                if wizard_action == 'create' and (wizard_contact or lead_partner):
                    self.assertEqual(lead.partner_id, wizard_contact or lead_partner)
                    self.assertFalse(lead.partner_id.parent_id)