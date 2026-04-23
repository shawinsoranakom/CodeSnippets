def _get_model_from_node(self, node, attr):
        """
        Look up a model from a <object model=...> or a <field rel=... to=...>
        node.
        """
        model_identifier = node.getAttribute(attr)
        if not model_identifier:
            raise base.DeserializationError(
                "<%s> node is missing the required '%s' attribute"
                % (node.nodeName, attr)
            )
        try:
            return apps.get_model(model_identifier)
        except (LookupError, TypeError):
            raise base.DeserializationError(
                "<%s> node has invalid model identifier: '%s'"
                % (node.nodeName, model_identifier)
            )