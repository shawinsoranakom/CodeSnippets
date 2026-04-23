def __setstate__(self, obj_dict):
        data = obj_dict.pop("_data", {})
        for k, v in data.items():
            self.setlist(k, v)
        self.__dict__.update(obj_dict)