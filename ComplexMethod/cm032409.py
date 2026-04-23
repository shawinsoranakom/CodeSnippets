def _transform_data(self):
        """Apply transformations to data based on instructions or input data."""
        # Get the data to transform
        transform_ref = self._param.transform_data
        if not transform_ref:
            self.set_output("summary", "No transform data reference provided")
            return

        data = self._canvas.get_variable_value(transform_ref)
        self.set_input_value(transform_ref, str(data)[:300] if data else "")

        if data is None:
            self.set_output("summary", "Transform data is empty")
            return

        # Convert to DataFrame
        if isinstance(data, dict):
            # Could be {"sheet": [rows]} format
            if all(isinstance(v, list) for v in data.values()):
                # Multiple sheets
                all_markdown = []
                for sheet_name, rows in data.items():
                    df = pd.DataFrame(rows)
                    all_markdown.append(f"### {sheet_name}\n\n{df.to_markdown(index=False)}")
                self.set_output("data", data)
                self.set_output("markdown", "\n\n".join(all_markdown))
            else:
                df = pd.DataFrame([data])
                self.set_output("data", df.to_dict(orient="records"))
                self.set_output("markdown", df.to_markdown(index=False))
        elif isinstance(data, list):
            df = pd.DataFrame(data)
            self.set_output("data", df.to_dict(orient="records"))
            self.set_output("markdown", df.to_markdown(index=False))
        else:
            self.set_output("data", {"raw": str(data)})
            self.set_output("markdown", str(data))

        self.set_output("summary", "Transformed data ready for processing")