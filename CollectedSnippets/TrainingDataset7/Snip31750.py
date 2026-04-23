def _get_field_values(serial_str, field_name):
        ret_list = []
        stream = StringIO(serial_str)
        for obj_dict in yaml.safe_load(stream):
            if "fields" in obj_dict and field_name in obj_dict["fields"]:
                field_value = obj_dict["fields"][field_name]
                # yaml.safe_load will return non-string objects for some
                # of the fields we are interested in, this ensures that
                # everything comes back as a string
                if isinstance(field_value, str):
                    ret_list.append(field_value)
                else:
                    ret_list.append(str(field_value))
        return ret_list