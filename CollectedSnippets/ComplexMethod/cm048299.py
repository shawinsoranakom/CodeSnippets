def _compute_email_phone(self):
        super(WebsiteVisitor, self)._compute_email_phone()

        for visitor in self.filtered(lambda visitor: not visitor.email or not visitor.mobile):
            linked_registrations = visitor.event_registration_ids.sorted(lambda reg: (reg.create_date, reg.id), reverse=False)
            if not visitor.email:
                visitor.email = next((reg.email for reg in linked_registrations if reg.email), False)
            if not visitor.mobile:
                visitor.mobile = next((reg.phone for reg in linked_registrations if reg.phone), False)