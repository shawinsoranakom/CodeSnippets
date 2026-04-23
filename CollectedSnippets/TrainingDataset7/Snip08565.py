def upload_interrupted(self):
        """
        Signal that the upload was interrupted. Subclasses should perform
        cleanup that is necessary for this handler.
        """
        pass