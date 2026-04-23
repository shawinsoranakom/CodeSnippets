def _check_currency_field(self):
        for rec in self:
            if rec.state == 'manual' and rec.ttype == 'monetary':
                if not rec.currency_field:
                    currency_field = self._get(rec.model, 'currency_id') or self._get(rec.model, 'x_currency_id')
                    if not currency_field:
                        raise ValidationError(_("Currency field is empty and there is no fallback field in the model"))
                else:
                    currency_field = self._get(rec.model, rec.currency_field)
                    if not currency_field:
                        raise ValidationError(_("Unknown field specified “%s” in currency_field", rec.currency_field))

                if currency_field.ttype != 'many2one':
                    raise ValidationError(_("Currency field does not have type many2one"))
                if currency_field.relation != 'res.currency':
                    raise ValidationError(_("Currency field should have a res.currency relation"))