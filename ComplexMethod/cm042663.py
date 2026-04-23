def _get_serialized_fields(
        self, item: Any, default_value: Any = None, include_empty: bool | None = None
    ) -> Iterable[tuple[str, Any]]:
        """Return the fields to export as an iterable of tuples
        (name, serialized_value)
        """
        item = ItemAdapter(item)

        if include_empty is None:
            include_empty = self.export_empty_fields

        if self.fields_to_export is None:
            field_iter = item.field_names() if include_empty else item.keys()
        elif isinstance(self.fields_to_export, Mapping):
            if include_empty:
                field_iter = self.fields_to_export.items()
            else:
                field_iter = (
                    (x, y) for x, y in self.fields_to_export.items() if x in item
                )
        elif include_empty:
            field_iter = self.fields_to_export
        else:
            field_iter = (x for x in self.fields_to_export if x in item)

        for field_name in field_iter:
            if isinstance(field_name, str):
                item_field, output_field = field_name, field_name
            else:
                item_field, output_field = field_name
            if item_field in item:
                field_meta = item.get_field_meta(item_field)
                value = self.serialize_field(field_meta, output_field, item[item_field])
            else:
                value = default_value

            yield output_field, value