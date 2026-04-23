def check_constraints(self, table_names=None):
        """
        Check constraints by setting them to immediate. Return them to deferred
        afterward.
        """
        with self.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")