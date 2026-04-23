def _get_field_values(serial_str, field_name):
        serial_list = json.loads(serial_str)
        return [
            obj_dict["fields"][field_name]
            for obj_dict in serial_list
            if field_name in obj_dict["fields"]
        ]