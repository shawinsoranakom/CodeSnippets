def _clean_sql_query(self, query: str) -> str:
        """Clean SQL query by removing surrounding quotes and whitespace.

        Also extracts SQL statements from text that might contain other content.

        Args:
            query: The SQL query to clean

        Returns:
            The cleaned SQL query
        """
        # First, try to extract SQL from code blocks
        sql_pattern = r"```(?:sql)?\s*([\s\S]*?)\s*```"
        sql_matches = re.findall(sql_pattern, query, re.IGNORECASE)

        if sql_matches:
            # If we found SQL in code blocks, use the first match
            query = sql_matches[0]
        else:
            # If no code block, try to find SQL statements
            # Look for common SQL keywords at the start of lines
            sql_keywords = r"(?i)(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH|MERGE)"
            lines = query.split("\n")
            sql_lines = []
            in_sql = False

            for _line in lines:
                line = _line.strip()
                if re.match(sql_keywords, line):
                    in_sql = True
                if in_sql:
                    sql_lines.append(line)
                if line.endswith(";"):
                    in_sql = False

            if sql_lines:
                query = "\n".join(sql_lines)

        # Remove any backticks that might be at the start or end
        query = query.strip("`")

        # Then remove surrounding quotes (single or double) if they exist
        query = query.strip()
        if (query.startswith('"') and query.endswith('"')) or (query.startswith("'") and query.endswith("'")):
            query = query[1:-1]

        # Finally, clean up any remaining whitespace and ensure no backticks remain
        query = query.strip()
        # Remove any remaining backticks, but preserve them if they're part of a table/column name
        # This regex will remove backticks that are not part of a valid identifier
        return re.sub(r"`(?![a-zA-Z0-9_])|(?<![a-zA-Z0-9_])`", "", query)