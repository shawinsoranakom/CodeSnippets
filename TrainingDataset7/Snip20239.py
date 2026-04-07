def articles_from_same_day_2(self):
        """
        Verbose version of get_articles_from_same_day_1, which does a custom
        database query for the sake of demonstration.
        """
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, headline, pub_date
                FROM custom_methods_article
                WHERE pub_date = %s
                    AND id != %s""",
                [connection.ops.adapt_datefield_value(self.pub_date), self.id],
            )
            return [self.__class__(*row) for row in cursor.fetchall()]