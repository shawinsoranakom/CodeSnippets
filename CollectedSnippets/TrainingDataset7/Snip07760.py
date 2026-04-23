def max_name_length(self):
        # Allow an index name longer than 30 characters when the suffix is
        # longer than the usual 3 character limit. The 30 character limit for
        # cross-database compatibility isn't applicable to PostgreSQL-specific
        # indexes.
        return Index.max_name_length - len(Index.suffix) + len(self.suffix)