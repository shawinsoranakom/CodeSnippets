def __init__(self, model, alias_cols=True):
        self.model = model
        self.alias_refcount = {}
        # alias_map is the most important data structure regarding joins.
        # It's used for recording which joins exist in the query and what
        # types they are. The key is the alias of the joined table (possibly
        # the table name) and the value is a Join-like object (see
        # sql.datastructures.Join for more information).
        self.alias_map = {}
        # Whether to provide alias to columns during reference resolving.
        self.alias_cols = alias_cols
        # Sometimes the query contains references to aliases in outer queries
        # (as a result of split_exclude). Correct alias quoting needs to know
        # these aliases too. Map external tables to whether they are aliased.
        self.external_aliases = {}
        self.table_map = {}  # Maps table names to list of aliases.
        self.used_aliases = set()

        self.where = WhereNode()
        # Maps alias -> Annotation Expression.
        self.annotations = {}
        # These are for extensions. The contents are more or less appended
        # verbatim to the appropriate clause.
        self.extra = {}  # Maps col_alias -> (col_sql, params).

        self._filtered_relations = {}