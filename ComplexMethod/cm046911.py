def _read_file_by_format(self, file_path, file_format):
        """Read file content based on detected format."""
        with open(file_path, "r", encoding = "utf-8") as f:
            if file_format == "plain_text" or file_format == "markdown":
                return f.read()
            elif file_format == "json_lines":
                lines = []
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        text = self._extract_text_from_json(data)
                        if text:
                            lines.append(text)
                    except json.JSONDecodeError:
                        continue
                return "\n\n".join(lines)
            elif file_format == "csv_text_column":
                reader = csv.DictReader(f)
                texts = []
                for row in reader:
                    text = self._extract_text_from_csv_row(row)
                    if text:
                        texts.append(text)
                return "\n\n".join(texts)
        return ""