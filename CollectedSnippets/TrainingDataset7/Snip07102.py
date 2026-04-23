def mean(self):
        """
        Return the mean of all pixel values of this band.
        """
        return self.statistics()[2]