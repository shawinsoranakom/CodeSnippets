def execute_sql(self) -> DataFrame:
        try:
            # First try to read the file
            try:
                service_account_path = Path(self.service_account_json_file)
                with service_account_path.open() as f:
                    credentials_json = json.load(f)
                    project_id = credentials_json.get("project_id")
                    if not project_id:
                        msg = "No project_id found in service account credentials file."
                        raise ValueError(msg)
            except FileNotFoundError as e:
                msg = f"Service account file not found: {e}"
                raise ValueError(msg) from e
            except json.JSONDecodeError as e:
                msg = "Invalid JSON string for service account credentials"
                raise ValueError(msg) from e

            # Then try to load credentials
            try:
                credentials = Credentials.from_service_account_file(self.service_account_json_file)
            except Exception as e:
                msg = f"Error loading service account credentials: {e}"
                raise ValueError(msg) from e

        except ValueError:
            raise
        except Exception as e:
            msg = f"Error executing BigQuery SQL query: {e}"
            raise ValueError(msg) from e

        try:
            client = bigquery.Client(credentials=credentials, project=project_id)

            # Check for empty or whitespace-only query before cleaning
            if not str(self.query).strip():
                msg = "No valid SQL query found in input text."
                raise ValueError(msg)

            # Always clean the query if it contains code block markers, quotes, or if clean_query is enabled
            if "```" in str(self.query) or '"' in str(self.query) or "'" in str(self.query) or self.clean_query:
                sql_query = self._clean_sql_query(str(self.query))
            else:
                sql_query = str(self.query).strip()  # At minimum, strip whitespace

            query_job = client.query(sql_query)
            results = query_job.result()
            output_dict = [dict(row) for row in results]

        except RefreshError as e:
            msg = "Authentication error: Unable to refresh authentication token. Please try to reauthenticate."
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"Error executing BigQuery SQL query: {e}"
            raise ValueError(msg) from e

        return DataFrame(output_dict)