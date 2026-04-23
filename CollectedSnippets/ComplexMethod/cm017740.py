def _handle_m2m_field_node(self, node, field):
        """
        Handle a <field> node for a ManyToManyField.
        """
        model = field.remote_field.model
        default_manager = model._default_manager
        if hasattr(default_manager, "get_by_natural_key"):

            def m2m_convert(n):
                keys = getChildrenByTagName(n, "natural")
                if keys:
                    # If there are 'natural' subelements, it must be a natural
                    # key
                    field_value = []
                    for k in keys:
                        if getChildrenByTagName(k, "None"):
                            field_value.append(None)
                        else:
                            field_value.append(getInnerText(k).strip())
                    obj_pk = (
                        default_manager.db_manager(self.db)
                        .get_by_natural_key(*field_value)
                        .pk
                    )
                else:
                    # Otherwise, treat like a normal PK value.
                    obj_pk = model._meta.pk.to_python(n.getAttribute("pk"))
                return obj_pk

        else:

            def m2m_convert(n):
                return model._meta.pk.to_python(n.getAttribute("pk"))

        values = []
        try:
            for c in getChildrenByTagName(node, "object"):
                values.append(m2m_convert(c))
        except SuspiciousOperation:
            raise
        except Exception as e:
            if isinstance(e, ObjectDoesNotExist) and self.handle_forward_references:
                return base.DEFER_FIELD
            else:
                raise base.M2MDeserializationError(e, c)
        else:
            return values