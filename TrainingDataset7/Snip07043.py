def num_feat(self, force=1):
        "Return the number of features in the Layer."
        return capi.get_feature_count(self.ptr, force)