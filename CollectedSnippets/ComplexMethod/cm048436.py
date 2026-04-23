def _get_aggregated_properties(self, move_line=False, move=False):
        move = move or move_line.move_id
        uom = move.product_uom or move_line.product_uom_id
        packaging_uom = move.packaging_uom_id
        name = move.product_id.display_name
        description = move.description_picking or ""
        product = move.product_id
        if description.startswith(name):
            description = description.removeprefix(name).strip()
        elif description.startswith(product.name):
            description = description.removeprefix(product.name).strip()
        line_key = f'{product.id}_{product.display_name}_{description or ""}_{uom.id}_{packaging_uom.id}'
        properties = {
            'line_key': line_key,
            'name': name,
            'description': description,
            'product_uom': uom,
            'packaging_uom_id': packaging_uom,
            'move': move,
        }
        if move_line and move_line.result_package_id:
            properties['package'] = move_line.result_package_id
            properties['package_history'] = move_line.package_history_id
            properties['line_key'] += f'_{move_line.result_package_id.id}'
        return properties