def _get_pk_values(serial_str):
        ret_list = []
        dom = minidom.parseString(serial_str)
        fields = dom.getElementsByTagName("object")
        for field in fields:
            ret_list.append(field.getAttribute("pk"))
        return ret_list