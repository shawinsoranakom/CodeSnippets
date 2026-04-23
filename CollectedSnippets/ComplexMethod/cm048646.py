def _compute_is_draft_duplicated_ref_ids(self):
        for move in self:
            move.is_draft_duplicated_ref_ids = any(duplicate_move.state == 'draft' for duplicate_move in move.duplicated_ref_ids)
            move.is_exact_move_duplicate = any(
                move.ref and move.ref == dup.ref
                and move.move_type == dup.move_type
                and move.partner_id == dup.partner_id
                and move.invoice_date == dup.invoice_date
                and move.amount_total == dup.amount_total
                and move.is_purchase_document()
                for dup in move.duplicated_ref_ids
            )