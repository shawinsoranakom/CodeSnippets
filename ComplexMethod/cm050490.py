def create(self, vals_list):
        # STEP: Remove the 'pos' fields from each vals.
        #   They will be written atomically to `pos_config_id` after the super call.
        pos_config_id_to_fields_vals_map = {}

        for vals in vals_list:
            pos_config_id = vals.get('pos_config_id')
            if pos_config_id:
                pos_fields_vals = {}

                if vals.get('pos_cash_rounding'):
                    vals['group_cash_rounding'] = True

                if vals.get('pos_use_pricelist'):
                    vals['group_product_pricelist'] = True

                if vals.get('pos_use_presets') is not None:
                    vals["group_pos_preset"] = bool(self.env["pos.config"].search_count([("use_presets", "=", True), ("id", "!=", pos_config_id)])) or vals['pos_use_presets']

                for field in self._fields.values():
                    if field.name == 'pos_config_id':
                        continue

                    val = vals.get(field.name)

                    # Add only to pos_fields_vals if
                    #   1. _field is in vals -- meaning, the _field is in view.
                    #   2. _field starts with 'pos_' -- meaning, the _field is a pos field.
                    if field.name.startswith('pos_') and val is not None:
                        pos_config_field_name = field.name[4:]
                        if not pos_config_field_name in self.env['pos.config']._fields:
                            _logger.warning("The value of '%s' is not properly saved to the pos_config_id field because the destination"
                                " field '%s' is not a valid field in the pos.config model.", field.name, pos_config_field_name)
                        else:
                            pos_fields_vals[pos_config_field_name] = val
                            del vals[field.name]

                pos_config_id_to_fields_vals_map[pos_config_id] = pos_fields_vals

        # STEP: Call super on the modified vals_list.
        # NOTE: When creating `res.config.settings` records, it doesn't write on *unmodified* related fields.
        result = super().create(vals_list)

        # STEP: Finally, we write the value of 'pos' fields to 'pos_config_id'.
        for pos_config_id, pos_fields_vals in pos_config_id_to_fields_vals_map.items():
            pos_config = self.env['pos.config'].browse(pos_config_id)
            pos_config.with_context(from_settings_view=True).write(pos_fields_vals)

        return result