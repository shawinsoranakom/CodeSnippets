def setFeature(self, name, state):
        if self._parsing:
            raise SAXNotSupportedException("Cannot set features while parsing")

        if name == feature_namespaces:
            self._namespaces = state
        elif name == feature_external_ges:
            self._external_ges = state
        elif name == feature_string_interning:
            if state:
                if self._interning is None:
                    self._interning = {}
            else:
                self._interning = None
        elif name == feature_validation:
            if state:
                raise SAXNotSupportedException(
                    "expat does not support validation")
        elif name == feature_external_pes:
            if state:
                raise SAXNotSupportedException(
                    "expat does not read external parameter entities")
        elif name == feature_namespace_prefixes:
            if state:
                raise SAXNotSupportedException(
                    "expat does not report namespace prefixes")
        else:
            raise SAXNotRecognizedException(
                "Feature '%s' not recognized" % name)