def compute_mask(self, _, mask):
        if isinstance(mask, list):
            mask = mask[0]
        if self.return_sequences:
            if not self.merge_mode:
                output_mask = (mask, mask)
            else:
                output_mask = mask
        else:
            output_mask = (None, None) if not self.merge_mode else None

        if self.return_state and self.states is not None:
            state_mask = (None for _ in self.states)
            if isinstance(output_mask, list):
                return output_mask + state_mask * 2
            return (output_mask,) + state_mask * 2
        return output_mask