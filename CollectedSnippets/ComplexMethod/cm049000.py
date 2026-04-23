def _get_sale_values(self, values):
        sale_values = {
            'chain_prev_document': self.company_id._get_l10n_es_tbai_last_chained_document(),
            **self._get_regime_code_value(values['taxes'], values['is_simplified']),
            **self._get_refunded_values(values),
        }
        # Regime key override for Canarias/Ceuta/Melilla and no_sujeto_loc
        if values['partner'] and values['partner'].country_id.code == 'ES' and values['partner'].state_id.code in ('TF', 'GC', 'CE', 'ME'):
            if any(t.l10n_es_type == 'no_sujeto_loc' for t in values['taxes']):
                sale_values.update({'regime_key': ['08']})

        if not values['partner'] or not values['partner']._l10n_es_is_foreign() or values["is_simplified"]:
            sale_values.update(**self._get_importe_desglose_es_partner(values['base_lines'], values['is_refund']))
        else:
            sale_values.update(**self._get_importe_desglose_foreign_partner(values['base_lines'], values['is_refund']))

        return sale_values