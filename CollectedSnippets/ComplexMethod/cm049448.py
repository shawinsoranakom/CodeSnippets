def _get_fiscal_state(move):
            """
            Maps each move to its corresponding fiscal state based on its type,
            fiscal conditions, and the state of the associated partner or company.
            """

            if (
                move.country_code != 'IN'
                or not move.is_invoice(include_receipts=True)
                # Partner's FP takes precedence through super
                or move.partner_shipping_id.property_account_position_id
                or move.partner_id.property_account_position_id
            ):
                return False
            elif move.l10n_in_gst_treatment == 'special_economic_zone':
                # Special Economic Zone
                return self.env.ref('l10n_in.state_in_oc')
            elif move.is_sale_document(include_receipts=True):
                # In Sales Documents: Compare place of supply with company state
                return move.l10n_in_state_id if move.l10n_in_state_id.l10n_in_tin != '96' else foreign_state
            elif move.is_purchase_document(include_receipts=True) and move.partner_id.country_id.code == 'IN':
                # In Purchases Documents: Compare place of supply with vendor state
                pos_state_id = move.l10n_in_state_id
                if pos_state_id.l10n_in_tin == '96':
                    return pos_state_id
                elif pos_state_id == move.partner_id.state_id:
                    # Intra-State: Group by state matching the company's state.
                    return move.company_id.state_id
                elif pos_state_id != move.partner_id.state_id:
                    # Inter-State: Group by state that doesn't match the company's state.
                    return (
                        pos_state_id == move.company_id.state_id
                        and move.partner_id.state_id
                        or pos_state_id
                    )
            return False