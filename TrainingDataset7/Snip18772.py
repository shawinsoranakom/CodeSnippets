def __init__(
        self, representation, referenced_tables, referenced_columns, referenced_indexes
    ):
        self.representation = representation
        self.referenced_tables = referenced_tables
        self.referenced_columns = referenced_columns
        self.referenced_indexes = referenced_indexes