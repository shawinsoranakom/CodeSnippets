def _get_pk_values(serial_str):
        ret_list = []
        stream = StringIO(serial_str)
        for obj_dict in yaml.safe_load(stream):
            ret_list.append(obj_dict["pk"])
        return ret_list