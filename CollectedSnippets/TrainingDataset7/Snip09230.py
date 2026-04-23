def _execute_create_test_db(self, cursor, parameters, keepdb=False):
        cursor.execute("CREATE DATABASE %(dbname)s %(suffix)s" % parameters)