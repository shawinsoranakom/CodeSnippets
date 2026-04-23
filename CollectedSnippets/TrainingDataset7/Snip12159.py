def explain_query(self):
        result = list(self.execute_sql())
        # Some backends return 1 item tuples with strings, and others return
        # tuples with integers and strings. Flatten them out into strings.
        format_ = self.query.explain_info.format
        output_formatter = json.dumps if format_ and format_.lower() == "json" else str
        for row in result:
            for value in row:
                if not isinstance(value, str):
                    yield " ".join([output_formatter(c) for c in value])
                else:
                    yield value