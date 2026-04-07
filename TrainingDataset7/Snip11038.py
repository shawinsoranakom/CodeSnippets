def db_type_parameters(self, connection):
        return DictWrapper(self.__dict__, connection.ops.quote_name, "qn_")