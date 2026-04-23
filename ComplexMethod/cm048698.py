def write(self, vals):
        # We allow any whitespace modifications in the subject
        normalized_subject = ' '.join(vals['subject'].split()) if vals.get('subject') else None
        if (
            vals.keys() & {'res_id', 'res_model', 'message_type', 'subtype_id'}
            or ('subject' in vals and any(' '.join(s.subject.split()) != normalized_subject for s in self if s.subject))
            or ('body' in vals and any(self.mapped('body')))
        ):
            self._except_audit_log()
        return super().write(vals)