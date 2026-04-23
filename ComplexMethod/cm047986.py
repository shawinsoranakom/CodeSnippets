def _filter_registrations(self, registrations):
        """ Keep registrations matching rule conditions. Those are

          * if a filter is set: filter registrations based on this filter. This is
            done like a search, and filter is a domain;
          * if a company is set on the rule, it must match event's company. Note
            that multi-company rules apply on event_lead_rule;
          * if an event category it set, it must match;
          * if an event is set, it must match;
          * if both event and category are set, one of them must match (OR). If none
            of those are set, it is considered as OK;

        :param registrations: event.registration recordset on which rule filters
          will be evaluated;
        :return: subset of registrations matching rules
        """
        self.ensure_one()
        if self.event_registration_filter and self.event_registration_filter != '[]':
            registrations = registrations.filtered_domain(literal_eval(self.event_registration_filter))

        # check from direct m2o to linked m2o / o2m to filter first without inner search
        company_ok = lambda registration: registration.company_id == self.company_id if self.company_id else True
        event_or_event_type_ok = \
            lambda registration: \
                registration.event_id == self.event_id or registration.event_id.event_type_id in self.event_type_ids \
                if (self.event_id or self.event_type_ids) else True

        return registrations.filtered(lambda r: company_ok(r) and event_or_event_type_ok(r))