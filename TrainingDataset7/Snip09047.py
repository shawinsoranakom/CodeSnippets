def _handle_object(self, node):
        """Convert an <object> node to a DeserializedObject."""
        # Look up the model using the model loading mechanism. If this fails,
        # bail.
        Model = self._get_model_from_node(node, "model")

        # Start building a data dictionary from the object.
        data = {}
        if node.hasAttribute("pk"):
            data[Model._meta.pk.attname] = Model._meta.pk.to_python(
                node.getAttribute("pk")
            )

        # Also start building a dict of m2m data (this is saved as
        # {m2m_accessor_attribute : [list_of_related_objects]})
        m2m_data = {}
        deferred_fields = {}

        field_names = {f.name for f in Model._meta.get_fields()}
        # Deserialize each field.
        for field_node in node.getElementsByTagName("field"):
            # If the field is missing the name attribute, bail (are you
            # sensing a pattern here?)
            field_name = field_node.getAttribute("name")
            if not field_name:
                raise base.DeserializationError(
                    "<field> node is missing the 'name' attribute"
                )

            # Get the field from the Model. This will raise a
            # FieldDoesNotExist if, well, the field doesn't exist, which will
            # be propagated correctly unless ignorenonexistent=True is used.
            if self.ignore and field_name not in field_names:
                continue
            field = Model._meta.get_field(field_name)

            # As is usually the case, relation fields get the special
            # treatment.
            if field.remote_field and isinstance(
                field.remote_field, models.ManyToManyRel
            ):
                value = self._handle_m2m_field_node(field_node, field)
                if value == base.DEFER_FIELD:
                    deferred_fields[field] = [
                        [
                            (
                                None
                                if nat_node.getElementsByTagName("None")
                                else getInnerText(nat_node).strip()
                            )
                            for nat_node in obj_node.getElementsByTagName("natural")
                        ]
                        for obj_node in field_node.getElementsByTagName("object")
                    ]
                else:
                    m2m_data[field.name] = value
            elif field.remote_field and isinstance(
                field.remote_field, models.ManyToOneRel
            ):
                value = self._handle_fk_field_node(field_node, field)
                if value == base.DEFER_FIELD:
                    deferred_fields[field] = [
                        (
                            None
                            if k.getElementsByTagName("None")
                            else getInnerText(k).strip()
                        )
                        for k in field_node.getElementsByTagName("natural")
                    ]
                else:
                    data[field.attname] = value
            else:
                if field_node.getElementsByTagName("None"):
                    value = None
                else:
                    value = field.to_python(getInnerText(field_node).strip())
                    # Load value since JSONField.to_python() outputs strings.
                    if field.get_internal_type() == "JSONField":
                        value = json.loads(value, cls=field.decoder)
                data[field.name] = value

        obj = base.build_instance(Model, data, self.db)

        # Return a DeserializedObject so that the m2m data has a place to live.
        return base.DeserializedObject(obj, m2m_data, deferred_fields)