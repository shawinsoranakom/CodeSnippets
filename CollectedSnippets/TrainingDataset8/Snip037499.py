def column_proto(normalized_weight: float) -> BlockProto:
            col_proto = BlockProto()
            col_proto.column.weight = normalized_weight
            col_proto.column.gap = gap_size
            col_proto.allow_empty = True
            return col_proto