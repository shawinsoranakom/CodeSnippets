def _compute_email_phone(self):
        super(WebsiteVisitor, self)._compute_email_phone()

        left_visitors = self.filtered(lambda visitor: not visitor.email or not visitor.mobile)
        leads = left_visitors.mapped('lead_ids').sorted('create_date', reverse=True)
        visitor_to_lead_ids = dict((visitor.id, visitor.lead_ids.ids) for visitor in left_visitors)

        for visitor in left_visitors:
            visitor_leads = leads.filtered(lambda lead: lead.id in visitor_to_lead_ids[visitor.id])
            if not visitor.email:
                visitor.email = next((lead.email_normalized for lead in visitor_leads if lead.email_normalized), False)
            if not visitor.mobile:
                visitor.mobile = next((lead.phone for lead in visitor_leads if lead.phone), False)