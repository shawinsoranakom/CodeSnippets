def _compute_display_name(self):
        """name that will be displayed in the detailed operation"""
        for record in self:
            if record.env.context.get('formatted_display_name'):
                name = f"{record.location_id.name}"
                if record.package_id:
                    name += f"\t--{record.package_id.display_name}--"
                if record.lot_id:
                    name += (' ' if record.package_id else '\t') + f"--{record.lot_id.name}--"
                record.display_name = name
            else:
                if not record.ids:
                    record.display_name = ''
                    continue
                name = [record.location_id.display_name]
                if record.lot_id:
                    name.append(record.lot_id.name)
                if record.package_id:
                    name.append(record.package_id.display_name)
                if record.owner_id:
                    name.append(record.owner_id.name)
                record.display_name = ' - '.join(name)