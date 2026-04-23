def set_values(self):
        super().set_values()
        if self.country_code == 'IN':
            if (
                not self.module_l10n_in_reports
                and (
                    self.l10n_in_fetch_vendor_edi_feature
                    or self.l10n_in_gst_efiling_feature
                    or self.l10n_in_enet_vendor_batch_payment_feature
                )
            ):
                self.module_l10n_in_reports = True
            for l10n_in_feature in (
                "l10n_in_fetch_vendor_edi_feature",
                "l10n_in_gst_efiling_feature",
                "l10n_in_enet_vendor_batch_payment_feature",
            ):
                if self[l10n_in_feature]:
                    self._update_l10n_in_feature(l10n_in_feature)
            if self.module_l10n_in_edi:
                self._update_l10n_in_feature("l10n_in_edi_feature")
            if self.module_l10n_in_ewaybill:
                self._update_l10n_in_feature("l10n_in_ewaybill_feature")