def _output_excel(self):
        """Generate Excel file output from data."""
        # Get data from transform_data reference
        transform_ref = self._param.transform_data
        if not transform_ref:
            self.set_output("summary", "No data reference for output")
            return

        data = self._canvas.get_variable_value(transform_ref)
        self.set_input_value(transform_ref, str(data)[:300] if data else "")

        if data is None:
            self.set_output("summary", "No data to output")
            return

        try:
            # Prepare DataFrames
            if isinstance(data, dict):
                if all(isinstance(v, list) for v in data.values()):
                    # Multi-sheet format
                    dfs = {k: pd.DataFrame(v) for k, v in data.items()}
                else:
                    dfs = {"Sheet1": pd.DataFrame([data])}
            elif isinstance(data, list):
                dfs = {"Sheet1": pd.DataFrame(data)}
            else:
                self.set_output("summary", "Invalid data format for Excel output")
                return

            # Generate output
            doc_id = get_uuid()

            if self._param.output_format == "csv":
                # For CSV, only output first sheet
                first_df = list(dfs.values())[0]
                binary_content = first_df.to_csv(index=False).encode("utf-8")
                filename = f"{self._param.output_filename}.csv"
            else:
                # Excel output
                excel_io = BytesIO()
                with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
                    for sheet_name, df in dfs.items():
                        # Sanitize sheet name (max 31 chars, no special chars)
                        safe_name = sheet_name[:31].replace("/", "_").replace("\\", "_")
                        df.to_excel(writer, sheet_name=safe_name, index=False)
                excel_io.seek(0)
                binary_content = excel_io.read()
                filename = f"{self._param.output_filename}.xlsx"

            # Store file
            settings.STORAGE_IMPL.put(self._canvas._tenant_id, doc_id, binary_content)

            # Set attachment output
            self.set_output("attachment", {
                "doc_id": doc_id,
                "format": self._param.output_format,
                "file_name": filename
            })

            total_rows = sum(len(df) for df in dfs.values())
            self.set_output("summary", f"Generated {filename} with {len(dfs)} sheet(s), {total_rows} total rows")
            self.set_output("data", {k: v.to_dict(orient="records") for k, v in dfs.items()})

            logging.info(f"ExcelProcessor: Generated {filename} as {doc_id}")

        except Exception as e:
            logging.error(f"ExcelProcessor output error: {e}")
            self.set_output("summary", f"Error generating output: {str(e)}")