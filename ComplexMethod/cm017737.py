def _handle_object(self, obj):
        data = {}
        m2m_data = {}
        deferred_fields = {}

        # Look up the model and starting build a dict of data for it.
        try:
            Model = self._get_model_from_node(obj["model"])
        except base.DeserializationError:
            if self.ignorenonexistent:
                return
            raise
        if "pk" in obj:
            try:
                data[Model._meta.pk.attname] = Model._meta.pk.to_python(obj.get("pk"))
            except Exception as e:
                raise base.DeserializationError.WithData(
                    e, obj["model"], obj.get("pk"), None
                )

        if Model not in self.field_names_cache:
            self.field_names_cache[Model] = {f.name for f in Model._meta.get_fields()}
        field_names = self.field_names_cache[Model]

        # Handle each field
        for field_name, field_value in obj["fields"].items():
            if self.ignorenonexistent and field_name not in field_names:
                # skip fields no longer on model
                continue

            field = Model._meta.get_field(field_name)

            # Handle M2M relations
            if field.remote_field and isinstance(
                field.remote_field, models.ManyToManyRel
            ):
                try:
                    values = self._handle_m2m_field_node(field, field_value)
                    if values == base.DEFER_FIELD:
                        deferred_fields[field] = field_value
                    else:
                        m2m_data[field.name] = values
                except base.M2MDeserializationError as e:
                    raise base.DeserializationError.WithData(
                        e.original_exc, obj["model"], obj.get("pk"), e.pk
                    )

            # Handle FK fields
            elif field.remote_field and isinstance(
                field.remote_field, models.ManyToOneRel
            ):
                try:
                    value = self._handle_fk_field_node(field, field_value)
                    if value == base.DEFER_FIELD:
                        deferred_fields[field] = field_value
                    else:
                        data[field.attname] = value
                except Exception as e:
                    raise base.DeserializationError.WithData(
                        e, obj["model"], obj.get("pk"), field_value
                    )

            # Handle all other fields
            else:
                try:
                    data[field.name] = field.to_python(field_value)
                except Exception as e:
                    raise base.DeserializationError.WithData(
                        e, obj["model"], obj.get("pk"), field_value
                    )

        model_instance = base.build_instance(Model, data, self.using)
        yield base.DeserializedObject(model_instance, m2m_data, deferred_fields)