def normalize_table_name(self, table_name):
                normalized_name = table_name.split(".")[1]
                if connection.features.ignores_table_name_case:
                    normalized_name = normalized_name.lower()
                return normalized_name