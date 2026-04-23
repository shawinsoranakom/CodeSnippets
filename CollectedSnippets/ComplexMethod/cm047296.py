def _check_order(self):
        for model in self:
            try:
                model._check_qorder(model.order)  # regex check for the whole clause ('is it valid sql?')
            except UserError as e:
                raise ValidationError(str(e))
            # add MAGIC_COLUMNS to 'stored_fields' in case 'model' has not been
            # initialized yet, or 'field_id' is not up-to-date in cache
            stored_fields = set(
                model.field_id.filtered('store').mapped('name') + models.MAGIC_COLUMNS
            )
            if model.model in self.env:
                # add fields inherited from models specified via code if they are already loaded
                stored_fields.update(
                    fname
                    for fname, fval in self.env[model.model]._fields.items()
                    if fval.inherited and fval.base_field.store
                )

            order_fields = RE_ORDER_FIELDS.findall(model.order)
            for field in order_fields:
                if field not in stored_fields:
                    raise ValidationError(_("Unable to order by %s: fields used for ordering must be present on the model and stored.", field))