def _get_m2m_db_table(self, opts):
        """
        Function that can be curried to provide the m2m table name for this
        relation.
        """
        if self.remote_field.through is not None:
            return self.remote_field.through._meta.db_table
        elif self.db_table:
            return self.db_table
        else:
            m2m_table_name = "%s_%s" % (utils.strip_quotes(opts.db_table), self.name)
            return utils.truncate_name(m2m_table_name, connection.ops.max_name_length())