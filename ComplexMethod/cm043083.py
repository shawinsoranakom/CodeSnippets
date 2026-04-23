def search(self, query: str, tables: List[str] = None) -> Dict[str, List[Dict]]:
        if not tables:
            tables = list(self.schema['tables'].keys())

        results = {}
        cursor = self.conn.cursor()

        for table in tables:
            # Search in text columns
            columns = self.schema['tables'][table]['columns']
            text_cols = [col for col, spec in columns.items()
                        if spec['type'] == 'TEXT' and col != 'id']

            if text_cols:
                where_clause = ' OR '.join([f"{col} LIKE ?" for col in text_cols])
                params = [f'%{query}%'] * len(text_cols)

                cursor.execute(f"SELECT * FROM {table} WHERE {where_clause} LIMIT 10", params)
                rows = cursor.fetchall()
                if rows:
                    results[table] = [dict(row) for row in rows]

        return results