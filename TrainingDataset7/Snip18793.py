def create_index_name(table_name, column_names, suffix):
            return ", ".join(
                "%s_%s_%s" % (table_name, column_name, suffix)
                for column_name in column_names
            )