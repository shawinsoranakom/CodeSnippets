def _unique_index_nulls_distinct_sql(self, nulls_distinct):
        if nulls_distinct is False:
            return " NULLS NOT DISTINCT"
        elif nulls_distinct is True:
            return " NULLS DISTINCT"
        return ""