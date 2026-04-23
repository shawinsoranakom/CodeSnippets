def _compute_custom_colors(self):
        for wizard in self:
            logo_primary = wizard.logo_primary_color or ''
            logo_secondary = wizard.logo_secondary_color or ''
            # Force lower case on color to ensure that FF01AA == ff01aa
            wizard.custom_colors = (
                wizard.logo and wizard.primary_color and wizard.secondary_color
                and not(
                    wizard.primary_color.lower() == logo_primary.lower()
                    and wizard.secondary_color.lower() == logo_secondary.lower()
                )
            )