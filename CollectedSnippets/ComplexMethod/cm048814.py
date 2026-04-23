def map_gs1_barcode(condition):
                if condition.field_expr != field or not nomenclature.is_gs1_nomenclature:
                    return condition
                # Check operator
                # handle `in` first and check the rest
                operator = condition.operator
                value = condition.value
                if not value:
                    return condition

                if operator in ('in', 'not in') and len(value) > 1:
                    sub_domain = Domain.OR(
                        map_gs1_barcode(Domain(field, '=', v))
                        for v in value
                    )
                    if operator == 'not in':
                        sub_domain = ~sub_domain
                    return sub_domain
                if operator in ('in', 'not in'):
                    operator = '=' if operator == 'in' else '!='
                    value = next(iter(value))
                elif operator not in ('ilike', 'not ilike', '=', '!='):
                    return condition

                # Parse the value
                if not value:
                    return condition
                try:
                    parsed_data = nomenclature.parse_barcode(value) or []
                except (ValidationError, ValueError):
                    parsed_data = []

                replacing_operator = 'ilike' if operator in ['ilike', '='] else 'not ilike'
                for data in parsed_data:
                    data_type = data['type']
                    value = data['value']
                    if data_type in barcode_types:
                        if data_type == 'lot':
                            return Domain(field, operator, value)
                        match = re.match('0*([0-9]+)$', str(value))
                        if match:
                            unpadded_barcode = match.groups()[0]
                            return Domain(field, replacing_operator, unpadded_barcode)
                        break

                # The barcode isn't a valid GS1 barcode, checks if it can be unpadded.
                if not parsed_data:
                    match = re.match('0+([0-9]+)$', value)
                    if match:
                        return Domain(field, replacing_operator, match.groups()[0])
                return condition