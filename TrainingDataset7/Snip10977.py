def get_group_by_cols(self):
        group_by_cols = []
        if self.partition_by:
            group_by_cols.extend(self.partition_by.get_group_by_cols())
        if self.order_by is not None:
            group_by_cols.extend(self.order_by.get_group_by_cols())
        return group_by_cols