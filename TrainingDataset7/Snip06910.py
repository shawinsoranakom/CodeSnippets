def layer_name(self):
        "Return the name of the layer for the feature."
        name = capi.get_feat_name(self._layer._ldefn)
        return force_str(name, self.encoding, strings_only=True)