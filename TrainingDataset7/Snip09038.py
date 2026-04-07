def start_object(self, obj):
        """
        Called as each object is handled.
        """
        if not hasattr(obj, "_meta"):
            raise base.SerializationError(
                "Non-model object (%s) encountered during serialization" % type(obj)
            )

        self.indent_level += 1
        self.indent(self.indent_level)
        attrs = {"model": str(obj._meta)}
        if not self.use_natural_primary_keys or not self._resolve_natural_key(obj):
            obj_pk = obj.pk
            if obj_pk is not None:
                attrs["pk"] = obj._meta.pk.value_to_string(obj)

        self.xml.startElement("object", attrs)