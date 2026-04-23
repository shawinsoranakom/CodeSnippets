def _create_or_update_table(self, table_name: str, columns: Dict):
        cursor = self.conn.cursor()

        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            # Create table
            col_defs = []
            for col_name, col_spec in columns.items():
                col_def = f"{col_name} {col_spec['type']}"
                if col_spec.get('primary'):
                    col_def += " PRIMARY KEY"
                if col_spec.get('autoincrement'):
                    col_def += " AUTOINCREMENT"
                if col_spec.get('unique'):
                    col_def += " UNIQUE"
                if col_spec.get('required'):
                    col_def += " NOT NULL"
                if 'default' in col_spec:
                    default = col_spec['default']
                    if default == 'CURRENT_TIMESTAMP':
                        col_def += f" DEFAULT {default}"
                    elif isinstance(default, str):
                        col_def += f" DEFAULT '{default}'"
                    else:
                        col_def += f" DEFAULT {default}"
                col_defs.append(col_def)

            create_sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
            cursor.execute(create_sql)
        else:
            # Check for new columns and add them
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}

            for col_name, col_spec in columns.items():
                if col_name not in existing_columns:
                    col_def = f"{col_spec['type']}"
                    if 'default' in col_spec:
                        default = col_spec['default']
                        if default == 'CURRENT_TIMESTAMP':
                            col_def += f" DEFAULT {default}"
                        elif isinstance(default, str):
                            col_def += f" DEFAULT '{default}'"
                        else:
                            col_def += f" DEFAULT {default}"

                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")

        self.conn.commit()