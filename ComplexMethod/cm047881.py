def _add_extra_in_forecast(self, forecast_lines, extras, product_rounding):
        if not extras:
            return forecast_lines

        lines_with_extras = []
        for forecast_line in forecast_lines:
            if forecast_line.get('document_in', False) or forecast_line.get('replenishment_filled'):
                lines_with_extras.append(forecast_line)
                continue
            line_qty = forecast_line['quantity']
            if forecast_line.get('document_out', False) and forecast_line['document_out']['_name'] == 'mrp.production':
                production_id = forecast_line['document_out']['id']
            else:
                production_id = False
            index_to_remove = []
            for index, extra in enumerate(extras):
                if float_is_zero(extra['quantity'], precision_rounding=product_rounding):
                    index_to_remove.append(index)
                    continue
                if production_id and extra.get('production_id', False) and extra['production_id'] != production_id:
                    continue
                if 'init_quantity' not in extra:
                    extra['init_quantity'] = extra['quantity']
                converted_qty = extra['uom']._compute_quantity(extra['quantity'], forecast_line['uom_id'])
                taken_from_extra = min(line_qty, converted_qty)
                ratio = taken_from_extra / extra['uom']._compute_quantity(extra['init_quantity'], forecast_line['uom_id'])
                line_qty -= taken_from_extra
                # Create copy of the current forecast line to add a possible replenishment.
                # Needs to be a copy since it might take multiple replenishment to fulfill a single "out" line.
                new_extra_line = copy.copy(forecast_line)
                new_extra_line['quantity'] = taken_from_extra
                new_extra_line['document_in'] = {
                    '_name': extra['_name'],
                    'id': extra['id'],
                }
                new_extra_line['cost'] = extra['cost'] * ratio
                lines_with_extras.append(new_extra_line)
                extra['quantity'] -= forecast_line['uom_id']._compute_quantity(taken_from_extra, extra['uom'])
                if float_compare(extra['quantity'], 0, precision_rounding=product_rounding) <= 0:
                    index_to_remove.append(index)
                if float_is_zero(line_qty, precision_rounding=product_rounding):
                    break

            for index in reversed(index_to_remove):
                del extras[index]

        return lines_with_extras