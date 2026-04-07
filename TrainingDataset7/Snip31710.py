def _get_pk_values(serial_str):
        serial_list = [json.loads(line) for line in serial_str.split("\n") if line]
        return [obj_dict["pk"] for obj_dict in serial_list]