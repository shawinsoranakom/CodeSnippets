def get_constraint_opclasses(self, constraint_name):
        with connection.cursor() as cursor:
            sql = """
                SELECT opcname
                FROM pg_opclass AS oc
                JOIN pg_index as i on oc.oid = ANY(i.indclass)
                JOIN pg_class as c on c.oid = i.indexrelid
                WHERE c.relname = %s
            """
            cursor.execute(sql, [constraint_name])
            return [row[0] for row in cursor.fetchall()]