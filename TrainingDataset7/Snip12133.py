def get_select_from_parent(cls, klass_info):
        for ki in klass_info["related_klass_infos"]:
            if ki["from_parent"]:
                ki["select_fields"] = klass_info["select_fields"] + ki["select_fields"]
            cls.get_select_from_parent(ki)