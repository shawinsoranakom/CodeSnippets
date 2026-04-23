def _get_records_data_list(self, records, fields):
        abstract_fields = [field for field in fields if isinstance(field, (dict, Store.Attr))]
        records_data_list = [
            [data_dict]
            for data_dict in records._read_format(
                [f for f in fields if f not in abstract_fields], load=False,
            )
        ]
        for record, record_data_list in zip(records, records_data_list):
            for field in abstract_fields:
                if isinstance(field, dict):
                    record_data_list.append(field)
                elif not field.predicate or field.predicate(record):
                    try:
                        record_data_list.append({field.field_name: field._get_value(record)})
                    except MissingError:
                        break
        return records_data_list