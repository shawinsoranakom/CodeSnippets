def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'confirmed':
            return self.env.ref('mrp.mrp_mo_in_confirmed')
        elif 'state' in init_values and self.state == 'progress':
            return self.env.ref('mrp.mrp_mo_in_progress')
        elif 'state' in init_values and self.state == 'to_close':
            return self.env.ref('mrp.mrp_mo_in_to_close')
        elif 'state' in init_values and self.state == 'done':
            return self.env.ref('mrp.mrp_mo_in_done')
        elif 'state' in init_values and self.state == 'cancel':
            return self.env.ref('mrp.mrp_mo_in_cancelled')
        return super()._track_subtype(init_values)