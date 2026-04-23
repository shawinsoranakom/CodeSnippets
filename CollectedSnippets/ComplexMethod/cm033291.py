def filter_scope_list(cls, in_key, in_filters_list, filters=None, cols=None):
        # Get records matching IN clause filters with optional column selection
        # Args:
        #     in_key: Field name for IN clause
        #     in_filters_list: List of values for IN clause
        #     filters: Additional filter conditions
        #     cols: List of columns to select
        # Returns:
        #     List of matching records
        in_filters_tuple_list = cls.cut_list(in_filters_list, 20)
        if not filters:
            filters = []
        res_list = []
        if cols:
            for i in in_filters_tuple_list:
                query_records = cls.model.select(*cols).where(getattr(cls.model, in_key).in_(i), *filters)
                if query_records:
                    res_list.extend([query_record for query_record in query_records])
        else:
            for i in in_filters_tuple_list:
                query_records = cls.model.select().where(getattr(cls.model, in_key).in_(i), *filters)
                if query_records:
                    res_list.extend([query_record for query_record in query_records])
        return res_list