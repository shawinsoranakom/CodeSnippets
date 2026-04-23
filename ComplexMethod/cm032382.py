def _convert_content(self, content):
        if not self._param.output_format:
            return

        import pypandoc
        doc_id = get_uuid()

        if self._param.output_format.lower() not in {"markdown", "html", "pdf", "docx", "xlsx"}:
            self._param.output_format = "markdown"

        try:
            if self._param.output_format in {"markdown", "html"}:
                if isinstance(content, str):
                    converted = pypandoc.convert_text(
                        content,
                        to=self._param.output_format,
                        format="markdown",
                    )
                else:
                    converted = pypandoc.convert_file(
                        content,
                        to=self._param.output_format,
                        format="markdown",
                    )

                binary_content = converted.encode("utf-8")

            elif self._param.output_format == "xlsx":
                import pandas as pd
                from io import BytesIO

                # Debug: log the content being parsed
                logging.info(f"XLSX Parser: Content length={len(content) if content else 0}, first 500 chars: {content[:500] if content else 'None'}")

                # Try to parse ALL Markdown tables from the content
                # Each table will be written to a separate sheet
                tables = []  # List of (sheet_name, dataframe)

                if isinstance(content, str):
                    lines = content.strip().split('\n')
                    logging.info(f"XLSX Parser: Total lines={len(lines)}, lines starting with '|': {sum(1 for line in lines if line.strip().startswith('|'))}")
                    current_table_lines = []
                    current_table_title = None
                    pending_title = None
                    in_table = False
                    table_count = 0

                    for i, line in enumerate(lines):
                        stripped = line.strip()

                        # Check for potential table title (lines before a table)
                        # Look for patterns like "Table 1:", "## Table", or markdown headers
                        if not in_table and stripped and not stripped.startswith('|'):
                            # Check if this could be a table title
                            lower_stripped = stripped.lower()
                            if (lower_stripped.startswith('table') or 
                                stripped.startswith('#') or
                                ':' in stripped):
                                pending_title = stripped.lstrip('#').strip()

                        if stripped.startswith('|') and '|' in stripped[1:]:
                            # Check if this is a separator line (|---|---|)
                            cleaned = stripped.replace(' ', '').replace('|', '').replace('-', '').replace(':', '')
                            if cleaned == '':
                                continue  # Skip separator line

                            if not in_table:
                                # Starting a new table
                                in_table = True
                                current_table_lines = []
                                current_table_title = pending_title
                                pending_title = None

                            current_table_lines.append(stripped)

                        elif in_table and not stripped.startswith('|'):
                            # End of current table - save it
                            if current_table_lines:
                                df = self._parse_markdown_table_lines(current_table_lines)
                                if df is not None and not df.empty:
                                    table_count += 1
                                    # Generate sheet name
                                    if current_table_title:
                                        # Clean and truncate title for sheet name
                                        sheet_name = current_table_title[:31]
                                        sheet_name = sheet_name.replace('/', '_').replace('\\', '_').replace('*', '').replace('?', '').replace('[', '').replace(']', '').replace(':', '')
                                    else:
                                        sheet_name = f"Table_{table_count}"
                                    tables.append((sheet_name, df))

                            # Reset for next table
                            in_table = False
                            current_table_lines = []
                            current_table_title = None

                            # Check if this line could be a title for the next table
                            if stripped:
                                lower_stripped = stripped.lower()
                                if (lower_stripped.startswith('table') or 
                                    stripped.startswith('#') or
                                    ':' in stripped):
                                    pending_title = stripped.lstrip('#').strip()

                    # Don't forget the last table if content ends with a table
                    if in_table and current_table_lines:
                        df = self._parse_markdown_table_lines(current_table_lines)
                        if df is not None and not df.empty:
                            table_count += 1
                            if current_table_title:
                                sheet_name = current_table_title[:31]
                                sheet_name = sheet_name.replace('/', '_').replace('\\', '_').replace('*', '').replace('?', '').replace('[', '').replace(']', '').replace(':', '')
                            else:
                                sheet_name = f"Table_{table_count}"
                            tables.append((sheet_name, df))

                # Fallback: if no tables found, create single sheet with content
                if not tables:
                    df = pd.DataFrame({"Content": [content if content else ""]})
                    tables = [("Data", df)]

                # Write all tables to Excel, each in a separate sheet
                excel_io = BytesIO()
                with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
                    used_names = set()
                    for sheet_name, df in tables:
                        # Ensure unique sheet names
                        original_name = sheet_name
                        counter = 1
                        while sheet_name in used_names:
                            suffix = f"_{counter}"
                            sheet_name = original_name[:31-len(suffix)] + suffix
                            counter += 1
                        used_names.add(sheet_name)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                excel_io.seek(0)
                binary_content = excel_io.read()

                logging.info(f"Generated Excel with {len(tables)} sheet(s): {[t[0] for t in tables]}")

            else:  # pdf, docx
                with tempfile.NamedTemporaryFile(suffix=f".{self._param.output_format}", delete=False) as tmp:
                    tmp_name = tmp.name

                try:
                    if isinstance(content, str):
                        pypandoc.convert_text(
                            content,
                            to=self._param.output_format,
                            format="markdown",
                            outputfile=tmp_name,
                        )
                    else:
                        pypandoc.convert_file(
                            content,
                            to=self._param.output_format,
                            format="markdown",
                            outputfile=tmp_name,
                        )

                    with open(tmp_name, "rb") as f:
                        binary_content = f.read()

                finally:
                    if os.path.exists(tmp_name):
                        os.remove(tmp_name)

            settings.STORAGE_IMPL.put(self._canvas._tenant_id, doc_id, binary_content)
            self.set_output("attachment", {
                "doc_id":doc_id,
                "format":self._param.output_format,
                "file_name":f"{doc_id[:8]}.{self._param.output_format}"})

            logging.info(f"Converted content uploaded as {doc_id} (format={self._param.output_format})")

        except Exception as e:
            logging.error(f"Error converting content to {self._param.output_format}: {e}")