def data_types_reverse(self):
        return {
            **super().data_types_reverse,
            oracledb.DB_TYPE_OBJECT: "GeometryField",
        }