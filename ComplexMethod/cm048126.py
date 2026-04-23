def write(self, vals):
        # Limitation: renaming a sparse field or changing the storing system is
        # currently not allowed
        if 'serialization_field_id' in vals or 'name' in vals:
            for field in self:
                if 'serialization_field_id' in vals and field.serialization_field_id.id != vals['serialization_field_id']:
                    raise UserError(_('Changing the storing system for field "%s" is not allowed.', field.name))
                if field.serialization_field_id and (field.name != vals['name']):
                    raise UserError(_('Renaming sparse field "%s" is not allowed', field.name))

        return super(IrModelFields, self).write(vals)