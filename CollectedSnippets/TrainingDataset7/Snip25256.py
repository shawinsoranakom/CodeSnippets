def test_include_partitions(self):
        """inspectdb --include-partitions creates models for partitions."""
        cursor_execute(
            """
            CREATE TABLE inspectdb_partition_parent (name text not null)
            PARTITION BY LIST (left(upper(name), 1))
            """,
            """
            CREATE TABLE inspectdb_partition_child
            PARTITION OF inspectdb_partition_parent
            FOR VALUES IN ('A', 'B', 'C')
            """,
        )
        self.addCleanup(
            cursor_execute,
            "DROP TABLE IF EXISTS inspectdb_partition_child",
            "DROP TABLE IF EXISTS inspectdb_partition_parent",
        )
        out = StringIO()
        partition_model_parent = "class InspectdbPartitionParent(models.Model):"
        partition_model_child = "class InspectdbPartitionChild(models.Model):"
        partition_managed = "managed = False  # Created from a partition."
        call_command("inspectdb", table_name_filter=inspectdb_tables_only, stdout=out)
        no_partitions_output = out.getvalue()
        self.assertIn(partition_model_parent, no_partitions_output)
        self.assertNotIn(partition_model_child, no_partitions_output)
        self.assertNotIn(partition_managed, no_partitions_output)
        call_command(
            "inspectdb",
            table_name_filter=inspectdb_tables_only,
            include_partitions=True,
            stdout=out,
        )
        with_partitions_output = out.getvalue()
        self.assertIn(partition_model_parent, with_partitions_output)
        self.assertIn(partition_model_child, with_partitions_output)
        self.assertIn(partition_managed, with_partitions_output)