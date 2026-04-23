def load_csv_to_data(self) -> list[Data]:
        if sum(bool(field) for field in [self.csv_file, self.csv_path, self.csv_string]) != 1:
            msg = "Please provide exactly one of: CSV file, file path, or CSV string."
            raise ValueError(msg)

        csv_data = None
        try:
            if self.csv_file:
                # FileInput always provides a local file path
                file_path = self.csv_file
                if not file_path.lower().endswith(".csv"):
                    self.status = "The provided file must be a CSV file."
                else:
                    # Resolve to absolute path and read from local filesystem
                    resolved_path = self.resolve_path(file_path)
                    csv_bytes = Path(resolved_path).read_bytes()
                    csv_data = csv_bytes.decode("utf-8")

            elif self.csv_path:
                file_path = self.csv_path
                if not file_path.lower().endswith(".csv"):
                    self.status = "The provided path must be to a CSV file."
                else:
                    csv_data = run_until_complete(
                        read_file_text(file_path, encoding="utf-8", resolve_path=self.resolve_path, newline="")
                    )

            else:
                csv_data = self.csv_string

            if csv_data:
                csv_reader = csv.DictReader(io.StringIO(csv_data))
                result = [Data(data=row, text_key=self.text_key) for row in csv_reader]

                if not result:
                    self.status = "The CSV data is empty."
                    return []

                self.status = result
                return result

        except csv.Error as e:
            error_message = f"CSV parsing error: {e}"
            self.status = error_message
            raise ValueError(error_message) from e

        except Exception as e:
            error_message = f"An error occurred: {e}"
            self.status = error_message
            raise ValueError(error_message) from e

        # An error occurred
        raise ValueError(self.status)