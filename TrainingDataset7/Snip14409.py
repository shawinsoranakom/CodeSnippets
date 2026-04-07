def write(self, outfile, encoding):
        """
        Output the feed in the given encoding to outfile, which is a file-like
        object. Subclasses should override this.
        """
        raise NotImplementedError(
            "subclasses of SyndicationFeed must provide a write() method"
        )