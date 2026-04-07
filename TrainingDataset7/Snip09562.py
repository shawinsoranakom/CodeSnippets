def sequence_reset_by_name_sql(self, style, sequences):
        return [
            "%s %s %s %s = 1;"
            % (
                style.SQL_KEYWORD("ALTER"),
                style.SQL_KEYWORD("TABLE"),
                style.SQL_FIELD(self.quote_name(sequence_info["table"])),
                style.SQL_FIELD("AUTO_INCREMENT"),
            )
            for sequence_info in sequences
        ]