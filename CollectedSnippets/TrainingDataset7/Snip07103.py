def std(self):
        """
        Return the standard deviation of all pixel values of this band.
        """
        return self.statistics()[3]