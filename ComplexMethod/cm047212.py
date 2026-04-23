def test_60_prefetch(self):
        """ Check the record cache prefetching """
        partners = self.env['res.partner'].search([('id', 'in', self.partners.ids)], limit=PREFETCH_MAX)
        self.assertTrue(len(partners) > 1)

        # all the records in partners are ready for prefetching
        self.assertItemsEqual(partners.ids, partners._prefetch_ids)

        # reading ONE partner should fetch them ALL
        for partner in partners:
            state = partner.state_id
            break
        partner_ids_with_field = [partner.id
                                  for partner in partners
                                  if 'state_id' in partner._cache]
        self.assertItemsEqual(partner_ids_with_field, partners.ids)

        # partners' states are ready for prefetching
        state_ids = {
            partner._cache['state_id']
            for partner in partners
            if partner._cache['state_id'] is not None
        }
        self.assertTrue(len(state_ids) > 1)
        self.assertItemsEqual(state_ids, state._prefetch_ids)

        # reading ONE partner country should fetch ALL partners' countries
        for partner in partners:
            if partner.state_id:
                partner.state_id.name
                break
        state_ids_with_field = [st.id for st in partners.state_id if 'name' in st._cache]
        self.assertItemsEqual(state_ids_with_field, state_ids)