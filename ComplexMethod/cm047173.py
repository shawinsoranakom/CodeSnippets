def remove_sign(tag_string, tag_signs, type_tax_use, document_type, tag2factor):
    tags = []
    if not tag_string:
        return tag_string
    for tag in tag_string.split('||'):
        tag = tag.strip()
        if not tag.startswith(('-', '+')):
            tags.append(tag)
            continue
        sign_str, new_tag = tag[0], tag[1:]
        tags.append(new_tag)

        if type_tax_use not in ('sale', 'purchase'):
            continue

        report_sign = 1 if sign_str == '+' else -1  # tax_negate
        if (type_tax_use, document_type) in [('sale', 'invoice'), ('purchase', 'refund')]:  # tax_tag_invert
            report_sign *= -1

        if existing_sign := tag_signs.get(new_tag):
            if existing_sign not in (report_sign, 'error'):
                tag_signs[new_tag] = 'error'
        else:
            tag_signs[new_tag] = report_sign

    return '||'.join(tags)