def load_onboarding_restaurant_scenario(self, with_demo_data=True):
        journal, payment_methods_ids = self._create_journal_and_payment_methods(cash_journal_vals={'name': _('Cash Restaurant'), 'show_on_dashboard': False})
        presets = self.get_record_by_ref([
            'pos_restaurant.pos_takein_preset',
            'pos_restaurant.pos_takeout_preset',
            'pos_restaurant.pos_delivery_preset',
        ]) + self.env['pos.preset'].search([]).ids
        config = self.env['pos.config'].create({
            'name': _('Restaurant'),
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'payment_method_ids': payment_methods_ids,
            'iface_splitbill': True,
            'module_pos_restaurant': True,
            'use_presets': bool(presets),
            'default_preset_id': presets[0] if presets else False,
            'available_preset_ids': [(6, 0, presets)],
        })
        self.env['ir.model.data']._update_xmlids([{
            'xml_id': self._get_suffixed_ref_name('pos_restaurant.pos_config_main_restaurant'),
            'record': config,
            'noupdate': True,
        }])
        if bool(presets):
            # Ensure the "Presets" menu is visible when installing the restaurant scenario
            self.env.ref("point_of_sale.group_pos_preset").implied_by_ids |= self.env.ref("base.group_user")
        if not self.env.ref('pos_restaurant.floor_main', raise_if_not_found=False):
            convert.convert_file(self._env_with_clean_context(), 'pos_restaurant', 'data/scenarios/restaurant_floor.xml', idref=None, mode='init', noupdate=True)
        config_floors = [(5, 0)]
        if (floor_main := self.env.ref('pos_restaurant.floor_main', raise_if_not_found=False)):
            config_floors += [(4, floor_main.id)]
        if (floor_patio := self.env.ref('pos_restaurant.floor_patio', raise_if_not_found=False)):
            config_floors += [(4, floor_patio.id)]
        config.update({'floor_ids': config_floors})
        config._load_restaurant_demo_data(with_demo_data)
        existing_session = self.env.ref('pos_restaurant.pos_closed_session_3', raise_if_not_found=False)
        if with_demo_data and self.env.company.id == self.env.ref('base.main_company').id and not existing_session:
            convert.convert_file(self._env_with_clean_context(), 'pos_restaurant', 'data/scenarios/restaurant_demo_session.xml', idref=None, mode='init', noupdate=True)
        return {'config_id': config.id}