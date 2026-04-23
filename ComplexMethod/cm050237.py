def _get_payment_context(self, response):
        """Extracts the payment context & other form info (provider & token ids)
        from a payment response

        :param response: http Response, with a payment form as text
        :return: Transaction context (+ provider_ids & token_ids)
        :rtype: dict
        """
        # Need to specify an HTML parser as parser
        # Otherwise void elements (<img>, <link> without a closing / tag)
        # are considered wrong and trigger a lxml.etree.XMLSyntaxError
        html_tree = objectify.fromstring(
            response.text,
            parser=etree.HTMLParser(),
        )
        payment_form = html_tree.xpath('//form[@id="o_payment_form"]')[0]
        values = {}
        for key, val in payment_form.items():
            if key.startswith("data-"):
                formatted_key = key[5:].replace('-', '_')
                if formatted_key.endswith('_id'):
                    formatted_val = int(val)
                elif formatted_key == 'amount':
                    formatted_val = float(val)
                else:
                    formatted_val = val
                values[formatted_key] = formatted_val

        payment_options_inputs = html_tree.xpath("//input[@name='o_payment_radio']")
        token_ids = []
        payment_method_ids = []
        for p_o_input in payment_options_inputs:
            data = dict()
            for key, val in p_o_input.items():
                if key.startswith('data-'):
                    data[key[5:]] = val
            if data['payment-option-type'] == 'token':
                token_ids.append(int(data['payment-option-id']))
            else:  # 'payment_method'
                payment_method_ids.append(int(data['payment-option-id']))

        values.update({
            'token_ids': token_ids,
            'payment_method_ids': payment_method_ids,
        })

        return values