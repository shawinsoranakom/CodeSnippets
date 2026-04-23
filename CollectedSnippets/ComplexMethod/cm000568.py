async def run(
        self, input_data: Input, *, execution_context: ExecutionContext, **_kwargs
    ) -> BlockOutput:
        import csv
        from io import StringIO

        # Determine data source - prefer file_input if provided, otherwise use contents
        if input_data.file_input:
            stored_file_path = await store_media_file(
                file=input_data.file_input,
                execution_context=execution_context,
                return_format="for_local_processing",
            )

            # Get full file path
            assert execution_context.graph_exec_id  # Validated by store_media_file
            file_path = get_exec_file_path(
                execution_context.graph_exec_id, stored_file_path
            )
            if not Path(file_path).exists():
                raise ValueError(f"File does not exist: {file_path}")

            # Check if file is an Excel file and convert to CSV
            file_extension = Path(file_path).suffix.lower()

            if file_extension in [".xlsx", ".xls"]:
                # Handle Excel files
                try:
                    from io import StringIO

                    import pandas as pd

                    # Read Excel file
                    df = pd.read_excel(file_path)

                    # Convert to CSV string
                    csv_buffer = StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_content = csv_buffer.getvalue()

                except ImportError:
                    raise ValueError(
                        "pandas library is required to read Excel files. Please install it."
                    )
                except Exception as e:
                    raise ValueError(f"Unable to read Excel file: {e}")
            else:
                # Handle CSV/text files
                csv_content = Path(file_path).read_text(encoding="utf-8")
        elif input_data.contents:
            # Use direct string content
            csv_content = input_data.contents
        else:
            raise ValueError("Either 'contents' or 'file_input' must be provided")

        csv_file = StringIO(csv_content)
        reader = csv.reader(
            csv_file,
            delimiter=input_data.delimiter,
            quotechar=input_data.quotechar,
            escapechar=input_data.escapechar,
        )

        header = None
        if input_data.has_header:
            header = next(reader)
            if input_data.strip:
                header = [h.strip() for h in header]

        for _ in range(input_data.skip_rows):
            next(reader)

        def process_row(row):
            data = {}
            for i, value in enumerate(row):
                if i not in input_data.skip_columns:
                    if input_data.has_header and header:
                        data[header[i]] = value.strip() if input_data.strip else value
                    else:
                        data[str(i)] = value.strip() if input_data.strip else value
            return data

        rows = [process_row(row) for row in reader]

        if input_data.produce_singular_result:
            for processed_row in rows:
                yield "row", processed_row
        else:
            yield "rows", rows