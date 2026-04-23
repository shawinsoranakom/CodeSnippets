def process_output(self) -> list[Data]:
        # Ensure metadata is a dictionary, filtering out any empty keys
        metadata = self._as_clean_dict(self.metadata)

        # Convert text_in to a Data object if it exists, and initialize our list of Data objects
        data_objects = [Data(text=self.text_in)] if self.text_in else []

        # Append existing Data objects from input_value, if any
        if self.input_value:
            data_objects.extend(self.input_value)

        # Update each Data object with the new metadata, preserving existing fields
        for data in data_objects:
            data.data.update(metadata)

        # Handle removal of fields specified in remove_fields
        if self.remove_fields:
            fields_to_remove = {field.strip() for field in self.remove_fields if field.strip()}

            # Remove specified fields from each Data object's metadata
            for data in data_objects:
                data.data = {k: v for k, v in data.data.items() if k not in fields_to_remove}

        # Set the status for tracking/debugging purposes
        self.status = data_objects
        return data_objects