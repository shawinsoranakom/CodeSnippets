def _build_jql(self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch) -> str:
        clauses: list[str] = []
        if self.jql_query:
            clauses.append(f"({self.jql_query})")
        elif self.project_key:
            clauses.append(f'project = "{self.project_key}"')
        else:
            raise ConnectorValidationError("Either project_key or jql_query must be provided for Jira connector.")

        if self.labels_to_skip:
            labels = ", ".join(f'"{label}"' for label in self.labels_to_skip)
            clauses.append(f"labels NOT IN ({labels})")

        adjusted_start = self._adjust_start_for_query(start)
        if adjusted_start is not None:
            clauses.append(f'updated >= "{self._format_jql_time(adjusted_start)}"')
        if end is not None:
            clauses.append(f'updated <= "{self._format_jql_time(end)}"')

        if not clauses:
            raise ConnectorValidationError("Unable to build Jira JQL query.")

        jql = " AND ".join(clauses)
        if "order by" not in jql.lower():
            jql = f"{jql} ORDER BY updated ASC"
        return jql