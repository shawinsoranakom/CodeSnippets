def __str__(self):
        if self.connection_reset:
            return "StopUpload: Halt current upload."
        else:
            return "StopUpload: Consume request data, then halt."