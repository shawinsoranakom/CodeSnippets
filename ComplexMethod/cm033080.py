def sql(self, sql: str, fetch_size: int, format: str):
        """
        Execute SQL query on Infinity database via psql command.
        Transform text-to-sql for Infinity's SQL syntax.
        """
        import subprocess

        try:
            self.logger.debug(f"InfinityConnection.sql get sql: {sql}")

            # Clean up SQL
            sql = re.sub(r"[ `]+", " ", sql)
            sql = sql.replace("%", "")

            # Transform SELECT field aliases to actual stored field names
            # Build field mapping from infinity_mapping.json comment field
            field_mapping = {}
            # Also build reverse mapping for column names in result
            reverse_mapping = {}
            fp_mapping = os.path.join(get_project_base_directory(), "conf", self.mapping_file_name)
            if os.path.exists(fp_mapping):
                with open(fp_mapping) as f:
                    schema = json.load(f)
                for field_name, field_info in schema.items():
                    if "comment" in field_info:
                        # Parse comma-separated aliases from comment
                        # e.g., "docnm_kwd, title_tks, title_sm_tks"
                        aliases = [a.strip() for a in field_info["comment"].split(",")]
                        for alias in aliases:
                            field_mapping[alias] = field_name
                            reverse_mapping[field_name] = alias  # Store first alias for reverse mapping

            # Replace field names in SELECT clause
            select_match = re.search(r"(select\s+.*?)(from\s+)", sql, re.IGNORECASE)
            if select_match:
                select_clause = select_match.group(1)
                from_clause = select_match.group(2)

                # Apply field transformations
                for alias, actual in field_mapping.items():
                    select_clause = re.sub(rf"(^|[, ]){alias}([, ]|$)", rf"\1{actual}\2", select_clause)

                sql = select_clause + from_clause + sql[select_match.end() :]

            # Also replace field names in WHERE, ORDER BY, GROUP BY, and HAVING clauses
            for alias, actual in field_mapping.items():
                # Transform in WHERE clause
                sql = re.sub(rf"(\bwhere\s+[^;]*?)(\b){re.escape(alias)}\b", rf"\1{actual}", sql, flags=re.IGNORECASE)
                # Transform in ORDER BY clause
                sql = re.sub(rf"(\border by\s+[^;]*?)(\b){re.escape(alias)}\b", rf"\1{actual}", sql, flags=re.IGNORECASE)
                # Transform in GROUP BY clause
                sql = re.sub(rf"(\bgroup by\s+[^;]*?)(\b){re.escape(alias)}\b", rf"\1{actual}", sql, flags=re.IGNORECASE)
                # Transform in HAVING clause
                sql = re.sub(rf"(\bhaving\s+[^;]*?)(\b){re.escape(alias)}\b", rf"\1{actual}", sql, flags=re.IGNORECASE)

            self.logger.debug(f"InfinityConnection.sql to execute: {sql}")

            # Get connection parameters from the Infinity connection pool wrapper
            # We need to use INFINITY_CONN singleton, not the raw ConnectionPool
            from common.doc_store.infinity_conn_pool import INFINITY_CONN

            conn_info = INFINITY_CONN.get_conn_uri()

            # Parse host and port from conn_info
            if conn_info and "host=" in conn_info:
                host_match = re.search(r"host=(\S+)", conn_info)
                if host_match:
                    host = host_match.group(1)
                else:
                    host = "infinity"
            else:
                host = "infinity"

            # Parse port from conn_info, default to 5432 if not found
            if conn_info and "port=" in conn_info:
                port_match = re.search(r"port=(\d+)", conn_info)
                if port_match:
                    port = port_match.group(1)
                else:
                    port = "5432"
            else:
                port = "5432"

            # Use psql command to execute SQL
            # Use full path to psql to avoid PATH issues
            psql_path = "/usr/bin/psql"
            # Check if psql exists at expected location, otherwise try to find it
            import shutil

            psql_from_path = shutil.which("psql")
            if psql_from_path:
                psql_path = psql_from_path

            # Execute SQL with psql to get both column names and data in one call
            psql_cmd = [
                psql_path,
                "-h",
                host,
                "-p",
                port,
                "-c",
                sql,
            ]

            self.logger.debug(f"Executing psql command: {' '.join(psql_cmd)}")

            result = subprocess.run(
                psql_cmd,
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                raise Exception(f"psql command failed: {error_msg}\nSQL: {sql}")

            # Parse the output
            output = result.stdout.strip()
            if not output:
                # No results
                return {"columns": [], "rows": []} if format == "json" else []

            # Parse psql table output which has format:
            #  col1 | col2 | col3
            #  -----+-----+-----
            #  val1 | val2 | val3
            lines = output.split("\n")

            # Extract column names from first line
            columns = []
            rows = []

            if len(lines) >= 1:
                header_line = lines[0]
                for col_name in header_line.split("|"):
                    col_name = col_name.strip()
                    if col_name:
                        columns.append({"name": col_name})

            # Data starts after the separator line (line with dashes)
            data_start = 2 if len(lines) >= 2 and "-" in lines[1] else 1
            for i in range(data_start, len(lines)):
                line = lines[i].strip()
                # Skip empty lines and footer lines like "(1 row)"
                if not line or re.match(r"^\(\d+ row", line):
                    continue
                # Split by | and strip each cell
                row = [cell.strip() for cell in line.split("|")]
                # Ensure row matches column count
                if len(row) == len(columns):
                    rows.append(row)
                elif len(row) > len(columns):
                    # Row has more cells than columns - truncate
                    rows.append(row[: len(columns)])
                elif len(row) < len(columns):
                    # Row has fewer cells - pad with empty strings
                    rows.append(row + [""] * (len(columns) - len(row)))

            if format == "json":
                result = {"columns": columns, "rows": rows[:fetch_size] if fetch_size > 0 else rows}
            else:
                result = rows[:fetch_size] if fetch_size > 0 else rows

            return result

        except subprocess.TimeoutExpired:
            self.logger.exception(f"InfinityConnection.sql timeout. SQL:\n{sql}")
            raise Exception(f"SQL timeout\n\nSQL: {sql}")
        except Exception as e:
            self.logger.exception(f"InfinityConnection.sql got exception. SQL:\n{sql}")
            raise Exception(f"SQL error: {e}\n\nSQL: {sql}")