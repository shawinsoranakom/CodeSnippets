def _mail_get_partner_fields(self, introspect_fields=False):
        """ This method returns the fields to use to find the contact to link
        when sending emails or notifications. Having partner is not always
        necessary but gives more flexibility to notifications management.

        :param bool introspect_fields: if no field is found by default
          heuristics, introspect model to find relational fields towards
          res.partner model. This is used notably when partners are
          mandatory like in voip;

        :return: list of valid field names that can be used to retrieve
          a partner (customer) on the record;
        """
        partner_fnames = [fname for fname in ('partner_id', 'partner_ids') if fname in self]
        if not partner_fnames and introspect_fields:
            partner_fnames = [
                fname for fname, fvalue in self._fields.items()
                if fvalue.type == 'many2one' and fvalue.comodel_name == 'res.partner'
            ]
        return partner_fnames