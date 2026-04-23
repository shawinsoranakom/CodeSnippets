def format_shipping_address(shipping_partner):
    """ Format the shipping address to comply with the payload structure of the API request.

    :param res.partner shipping_partner: The shipping partner.
    :return: The formatted shipping address.
    :rtype: dict
    """
    return {
        'shipping[address][city]': shipping_partner.city or '',
        'shipping[address][country]': shipping_partner.country_id.code or '',
        'shipping[address][line1]': shipping_partner.street or '',
        'shipping[address][line2]': shipping_partner.street2 or '',
        'shipping[address][postal_code]': shipping_partner.zip or '',
        'shipping[address][state]': shipping_partner.state_id.name or '',
        'shipping[name]': shipping_partner.name or shipping_partner.parent_id.name or '',
    }