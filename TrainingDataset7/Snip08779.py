def reset_sequences(self, connection, models):
        """Reset database sequences for the given connection and models."""
        sequence_sql = connection.ops.sequence_reset_sql(no_style(), models)
        if sequence_sql:
            if self.verbosity >= 2:
                self.stdout.write("Resetting sequences")
            with connection.cursor() as cursor:
                for line in sequence_sql:
                    cursor.execute(line)