def _get_no_autofield_sequence_name(self, table):
        """
        Manually created sequence name to keep backward compatibility for
        AutoFields that aren't Oracle identity columns.
        """
        name_length = self.max_name_length() - 3
        return "%s_SQ" % truncate_name(strip_quotes(table), name_length).upper()