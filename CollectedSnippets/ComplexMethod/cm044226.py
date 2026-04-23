def model_serialize(self):
        """Return the serialized data."""
        data: dict = {}
        for field in self.model_fields:
            value = getattr(self, field)
            if isinstance(value, list):
                if value:  # Check if the list is not empty
                    if isinstance(value[0], datetime):
                        data[field] = [str(v) if v else None for v in value]
                    else:
                        data[field] = value
            else:
                data[field] = value

        records = [dict(zip(data.keys(), values)) for values in zip(*data.values())]

        return records