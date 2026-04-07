def get_kwargs_str(field_name):
        kwlist = []
        if field_name.lower() in null_fields:
            kwlist.append("null=True")
        if field_name.lower() in blank_fields:
            kwlist.append("blank=True")
        if kwlist:
            return ", " + ", ".join(kwlist)
        else:
            return ""