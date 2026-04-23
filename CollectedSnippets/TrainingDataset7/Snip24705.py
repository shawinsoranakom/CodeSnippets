def __getattribute__(self, name):
            if name != vendor_impl:
                return __getattribute__original(self, name)
            try:
                as_sql = __getattribute__original(self, vendor_impl)
            except AttributeError:
                as_sql = __getattribute__original(self, "as_sql")
            return as_sql_wrapper(as_sql)