def add_form_signature(html_fragment, env_sudo):
    for form in html_fragment.iter('form'):
        if '/website/form/' not in form.attrib.get('action', ''):
            continue

        existing_hash_node = form.find('.//input[@type="hidden"][@name="website_form_signature"]')
        if existing_hash_node is not None:
            existing_hash_node.getparent().remove(existing_hash_node)
        input_nodes = form.xpath('.//input[contains(@name, "email_")]')
        form_values = {input_node.attrib['name']: input_node for input_node in input_nodes}
        # if this form does not send an email, ignore. But at this stage,
        # the value of email_to can still be None in case of default value
        if 'email_to' not in form_values:
            continue

        email_to_value = form_values['email_to'].attrib.get('value')
        if (not email_to_value
            or (email_to_value == 'info@yourcompany.example.com'
                and html_fragment.xpath('//span[@data-for="contactus_form"]')
                and html_fragment.xpath('//form[@id="contactus_form"]'))):
            # This means that the mail will be sent to the value of the dataFor
            # which is the company email.
            email_to_value = env_sudo.company.email or ''

        has_cc = {'email_cc', 'email_bcc'} & form_values.keys()
        value = email_to_value + (':email_cc' if has_cc else '')
        hash_value = hmac(env_sudo, 'website_form_signature', value)
        if has_cc:
            hash_value += ':email_cc'
        hash_node = etree.Element('input', attrib={'type': "hidden", 'value': hash_value, 'class': "form-control s_website_form_input s_website_form_custom", 'name': "website_form_signature"})
        form_values['email_to'].addnext(hash_node)