def _check_serial_number(self, product_id, lot_id, company_id, source_location_id=None, ref_doc_location_id=None):
        """ Checks for duplicate serial numbers (SN) when assigning a SN (i.e. no source_location_id)
        and checks for potential incorrect location selection of a SN when using a SN (i.e.
        source_location_id). Returns warning message of all locations the SN is located at and
        (optionally) a recommended source location of the SN (when using SN from incorrect location).
        This function is designed to be used by onchange functions across differing situations including,
        but not limited to scrap, incoming picking SN encoding, and outgoing picking SN selection.

        :param product_id: `product.product` product to check SN for
        :param lot_id: `stock.production.lot` SN to check
        :param company_id: `res.company` company to check against (i.e. we ignore duplicate SNs across
            different companies for lots defined with a company)
        :param source_location_id: `stock.location` optional source location if using the SN rather
            than assigning it
        :param ref_doc_location_id: `stock.location` optional reference document location for
            determining recommended location. This is param expected to only be used when a
            `source_location_id` is provided.
        :return: tuple(message, recommended_location) If not None, message is a string expected to be
            used in warning message dict and recommended_location is a `location_id`
        """
        message = None
        recommended_location = None
        if product_id.tracking == 'serial':
            internal_domain = Domain('location_id.usage', 'in', ('internal', 'transit'))
            if lot_id.company_id:
                internal_domain &= Domain('company_id', '=', company_id.id)
            quants = self.env['stock.quant'].search(Domain.AND((
                Domain('product_id', '=', product_id.id),
                Domain('lot_id', 'in', lot_id.ids),
                Domain('quantity', '!=', 0),
                Domain('location_id.usage', '=', 'customer') | internal_domain,
            )))
            sn_locations = quants.mapped('location_id')
            if quants:
                if not source_location_id:
                    # trying to assign an already existing SN
                    message = _('The Serial Number (%(serial_number)s) is already used in location(s): %(location_list)s.\n\n'
                                'Is this expected? For example, this can occur if a delivery operation is validated '
                                'before its corresponding receipt operation is validated. In this case the issue will be solved '
                                'automatically once all steps are completed. Otherwise, the serial number should be corrected to '
                                'prevent inconsistent data.',
                                serial_number=lot_id.name, location_list=sn_locations.mapped('display_name'))

                elif source_location_id and source_location_id not in sn_locations:
                    # using an existing SN in the wrong location
                    recommended_location = self.env['stock.location']
                    if ref_doc_location_id:
                        for location in sn_locations:
                            if ref_doc_location_id.parent_path in location.parent_path:
                                recommended_location = location
                                break
                    else:
                        for location in sn_locations:
                            if location.usage != 'customer':
                                recommended_location = location
                                break
                    if recommended_location and recommended_location.company_id == company_id:
                        message = _('Serial number (%(serial_number)s) is not located in %(source_location)s, but is located in location(s): %(other_locations)s.\n\n'
                                    'Source location for this move will be changed to %(recommended_location)s',
                                    serial_number=lot_id.name,
                                    source_location=source_location_id.display_name,
                                    other_locations=sn_locations.mapped('display_name'),
                                    recommended_location=recommended_location.display_name)
                    else:
                        message = _('Serial number (%(serial_number)s) is not located in %(source_location)s, but is located in location(s): %(other_locations)s.\n\n'
                                    'Please correct this to prevent inconsistent data.',
                                    serial_number=lot_id.name,
                                    source_location=source_location_id.display_name,
                                    other_locations=sn_locations.mapped('display_name'))
                        recommended_location = None
        return message, recommended_location