def sql(self, sql: str, fetch_size: int = 1024, format: str = "json"):
        logger.debug("OBConnection.sql get sql: %s", sql)

        def normalize_sql(sql_text: str) -> str:
            cleaned = sql_text.strip().rstrip(";")
            cleaned = re.sub(r"[`]+", "", cleaned)
            cleaned = re.sub(
                r"json_extract_string\s*\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)",
                r"JSON_UNQUOTE(JSON_EXTRACT(\1, \2))",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = re.sub(
                r"json_extract_isnull\s*\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)",
                r"(JSON_EXTRACT(\1, \2) IS NULL)",
                cleaned,
                flags=re.IGNORECASE,
            )
            return cleaned

        def coerce_value(value: Any) -> Any:
            if isinstance(value, np.generic):
                return value.item()
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="ignore")
            return value

        sql_text = normalize_sql(sql)
        if fetch_size and fetch_size > 0:
            sql_lower = sql_text.lstrip().lower()
            if re.match(r"^(select|with)\b", sql_lower) and not re.search(r"\blimit\b", sql_lower):
                sql_text = f"{sql_text} LIMIT {int(fetch_size)}"

        logger.debug("OBConnection.sql to ob: %s", sql_text)

        try:
            res = self.client.perform_raw_text_sql(sql_text)
        except Exception:
            logger.exception("OBConnection.sql got exception")
            raise

        if res is None:
            return None

        columns = list(res.keys()) if hasattr(res, "keys") else []
        try:
            rows = res.fetchmany(fetch_size) if fetch_size and fetch_size > 0 else res.fetchall()
        except Exception:
            rows = res.fetchall()

        rows_list = [[coerce_value(v) for v in list(row)] for row in rows]
        result = {
            "columns": [{"name": col, "type": "text"} for col in columns],
            "rows": rows_list,
        }

        if format == "markdown":
            header = "|" + "|".join(columns) + "|" if columns else ""
            separator = "|" + "|".join(["---" for _ in columns]) + "|" if columns else ""
            body = "\n".join(["|" + "|".join([str(v) for v in row]) + "|" for row in rows_list])
            result["markdown"] = "\n".join([line for line in [header, separator, body] if line])

        return result