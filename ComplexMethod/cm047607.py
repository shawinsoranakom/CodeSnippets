def fill_properties_cache(records, fnames_by_path, fname):
                """ Fill the cache for the ``fname`` properties field and return it """
                cache_properties_field = cache_properties[records._fields[fname]]

                # read properties to have all the logic of Properties.convert_to_read_multi
                for row in records.read([fname]):
                    properties = row[fname]
                    if not properties:
                        continue
                    rec_id = row['id']

                    for property in properties:
                        current_prop_name = property['name']
                        if f"{fname}.{current_prop_name}" not in fnames_by_path:
                            continue
                        property_type = property['type']
                        if current_prop_name not in cache_properties_field:
                            cache_properties_field[current_prop_name] = [property_type, {}]

                        __, cache_by_id = cache_properties_field[current_prop_name]
                        if rec_id in cache_by_id:
                            continue

                        value = property.get('value')
                        if property_type in ('many2one', 'many2many'):
                            if not isinstance(value, list):
                                value = [value] if value else []
                            value = self.env[property['comodel']].browse([val[0] for val in value])
                        elif property_type == 'tags' and value:
                            value = ",".join(
                                next(iter(tag[1] for tag in property['tags'] if tag[0] == v), '')
                                for v in value
                            )
                        elif property_type == 'selection':
                            value = dict(property['selection']).get(value, '')
                        cache_by_id[rec_id] = value