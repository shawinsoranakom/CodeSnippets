def get_name(line):
            values = []
            if line.move_id.partner_id.lang:
                product = line.product_id.with_context(lang=line.move_id.partner_id.lang)
            elif line.partner_id.lang:
                product = line.product_id.with_context(lang=line.partner_id.lang)
            else:
                product = line.product_id
            if not product:
                return False

            if line.journal_id.type == 'sale':
                values.append(product.display_name)
                if product.description_sale:
                    values.append(product.description_sale)
            elif line.journal_id.type == 'purchase':
                values.append(product.display_name)
                if product.description_purchase:
                    values.append(product.description_purchase)
            return '\n'.join(values) if values else False