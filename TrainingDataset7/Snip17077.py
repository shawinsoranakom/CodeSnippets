def test_annotate_with_extra(self):
        """
        Regression test for #11916: Extra params + aggregation creates
        incorrect SQL.
        """
        # Oracle doesn't support subqueries in group by clause
        shortest_book_sql = """
        SELECT name
        FROM aggregation_regress_book b
        WHERE b.publisher_id = aggregation_regress_publisher.id
        ORDER BY b.pages
        LIMIT 1
        """
        # tests that this query does not raise a DatabaseError due to the full
        # subselect being (erroneously) added to the GROUP BY parameters
        qs = Publisher.objects.extra(
            select={
                "name_of_shortest_book": shortest_book_sql,
            }
        ).annotate(total_books=Count("book"))
        # force execution of the query
        list(qs)