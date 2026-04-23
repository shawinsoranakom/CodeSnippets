def _get_pk_values(serial_str):
        serial_list = json.loads(serial_str)
        return [obj_dict["pk"] for obj_dict in serial_list]