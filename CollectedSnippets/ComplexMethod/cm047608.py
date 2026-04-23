def fetch_fields(records, field_paths):
                """ Fill the cache of ``records`` for all ``field_paths`` recursively included properties"""
                if not records:
                    return

                fnames_by_path = dict(groupby(
                    [path for path in field_paths if path and path[0] not in ('id', '.id')],
                    lambda path: path[0],
                ))

                # Fetch needed fields (remove '.property_name' part)
                fnames = list(unique(fname.split('.')[0] for fname in fnames_by_path))
                records.fetch(fnames)
                # Fill the cache of the properties field
                for fname in fnames:
                    field = records._fields[fname]
                    if field.type == 'properties':
                        fill_properties_cache(records, fnames_by_path, fname)

                # Call it recursively for relational field (included property relational field)
                for fname, paths in fnames_by_path.items():
                    if '.' in fname:  # Properties field
                        fname, prop_name = fname.split('.')
                        field = records._fields[fname]
                        assert field.type == 'properties' and prop_name

                        property_type, property_cache = cache_properties[field].get(prop_name, ('char', None))
                        if property_type not in ('many2one', 'many2many') or not property_cache:
                            continue
                        model = next(iter(property_cache.values())).browse()
                        subrecords = model.union(*[property_cache[rec_id] for rec_id in records.ids if rec_id in property_cache])
                    else:  # Normal field
                        field = records._fields[fname]
                        if not field.relational:
                            continue
                        subrecords = records[fname]

                    paths = [path[1:] or ['display_name'] for path in paths]
                    fetch_fields(subrecords, paths)