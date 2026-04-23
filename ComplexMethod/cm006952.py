def convert_json_to_data(self) -> Data | list[Data]:
        if sum(bool(field) for field in [self.json_file, self.json_path, self.json_string]) != 1:
            msg = "Please provide exactly one of: JSON file, file path, or JSON string."
            self.status = msg
            raise ValueError(msg)

        json_data = None

        try:
            if self.json_file:
                # FileInput always provides a local file path
                file_path = self.json_file
                if not file_path.lower().endswith(".json"):
                    self.status = "The provided file must be a JSON file."
                else:
                    # Resolve to absolute path and read from local filesystem
                    resolved_path = self.resolve_path(file_path)
                    json_data = Path(resolved_path).read_text(encoding="utf-8")

            elif self.json_path:
                # User-provided text path - could be local or S3 key
                file_path = self.json_path
                if not file_path.lower().endswith(".json"):
                    self.status = "The provided path must be to a JSON file."
                else:
                    json_data = run_until_complete(
                        read_file_text(file_path, encoding="utf-8", resolve_path=self.resolve_path)
                    )

            else:
                json_data = self.json_string

            if json_data:
                # Try to parse the JSON string
                try:
                    parsed_data = json.loads(json_data)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to repair the JSON string
                    repaired_json_string = repair_json(json_data)
                    parsed_data = json.loads(repaired_json_string)

                # Check if the parsed data is a list
                if isinstance(parsed_data, list):
                    result = [Data(data=item) for item in parsed_data]
                else:
                    result = Data(data=parsed_data)
                self.status = result
                return result

        except (json.JSONDecodeError, SyntaxError, ValueError) as e:
            error_message = f"Invalid JSON or Python literal: {e}"
            self.status = error_message
            raise ValueError(error_message) from e

        except Exception as e:
            error_message = f"An error occurred: {e}"
            self.status = error_message
            raise ValueError(error_message) from e

        # An error occurred
        raise ValueError(self.status)