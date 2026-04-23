def create(self, vals_list):
        for vals in vals_list:
            is_restaurant = 'module_pos_restaurant' in vals and vals['module_pos_restaurant']
            if is_restaurant:
                if 'iface_printbill' not in vals:
                    vals['iface_printbill'] = True
                if 'show_product_images' not in vals:
                    vals['show_product_images'] = False
                if 'show_category_images' not in vals:
                    vals['show_category_images'] = False
            if not is_restaurant or not vals.get('iface_tipproduct', False):
                vals['set_tip_after_payment'] = False
        pos_configs = super().create(vals_list)
        for config in pos_configs:
            if config.module_pos_restaurant:
                self._setup_default_floor(config)
        return pos_configs