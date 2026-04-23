def _update_values(self, src_partners, dst_partner):
        """ Update values of dst_partner with the ones from the src_partners.
            :param src_partners : recordset of source res.partner
            :param dst_partner : record of destination res.partner
        """
        _logger.debug('_update_values for dst_partner: %s for src_partners: %r', dst_partner.id, src_partners.ids)

        model_fields = dst_partner.fields_get().keys()
        summable_fields = self._get_summable_fields()

        def write_serializer(item):
            if isinstance(item, models.BaseModel):
                return item.id
            else:
                return item

        # get all fields that are not computed or x2many
        values = dict()
        values_by_company = defaultdict(dict)   # {company: vals}
        for column in model_fields:
            field = dst_partner._fields[column]
            if field.type not in ('many2many', 'one2many') and field.compute is None:
                for item in itertools.chain(src_partners, [dst_partner]):
                    if item[column]:
                        if field.type == 'reference':
                            values[column] = item[column]
                        elif column in summable_fields and values.get(column):
                            values[column] += write_serializer(item[column])
                        else:
                            values[column] = write_serializer(item[column])
            elif field.company_dependent and column in summable_fields:
                # sum the values of partners for each company; use sudo() to
                # compute the sum on all companies, including forbidden ones
                partners = (src_partners + dst_partner).sudo()
                for company in self.env['res.company'].sudo().search([]):
                    values_by_company[company][column] = sum(
                        partners.with_company(company).mapped(column)
                    )

        # remove fields that can not be updated (id and parent_id)
        values.pop('id', None)
        parent_id = values.pop('parent_id', None)
        dst_partner.write(values)
        for company, vals in values_by_company.items():
            dst_partner.with_company(company).sudo().write(vals)
        # try to update the parent_id
        if parent_id and parent_id != dst_partner.id:
            try:
                dst_partner.write({'parent_id': parent_id})
            except ValidationError:
                _logger.info('Skip recursive partner hierarchies for parent_id %s of partner: %s', parent_id, dst_partner.id)