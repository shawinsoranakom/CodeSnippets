def _compute_l10n_gr_edi_available_cls_category(self):
        for line in self:
            inv_type = line.move_id.l10n_gr_edi_inv_type

            # we need inv_type to calculate available_cls_category
            if not inv_type or (
                    inv_type
                    and CLASSIFICATION_MAP[inv_type] == 'associate'
                    and not line.move_id.l10n_gr_edi_correlation_id
            ):  # associate inv_type must have a correlation_id, otherwise inv_type is considered empty
                line.l10n_gr_edi_available_cls_category = False
                continue

            if CLASSIFICATION_MAP[inv_type] == 'associate':
                inv_type = line.move_id.l10n_gr_edi_correlation_id.l10n_gr_edi_inv_type

            is_income = (
                line.move_type in ('out_invoice', 'out_refund')
                and inv_type not in TYPES_WITH_SEND_EXPENSE
                and (not line.l10n_gr_edi_detail_type or line.l10n_gr_edi_detail_type == '2')
            )

            line.l10n_gr_edi_available_cls_category = self.env['l10n_gr_edi.preferred_classification']._get_l10n_gr_edi_available_cls_category(
                inv_type=inv_type, category_type='1' if is_income else '2')