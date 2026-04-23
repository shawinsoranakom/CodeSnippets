def num_fields(self):
        "Return the number of fields in the Feature."
        return capi.get_feat_field_count(self.ptr)