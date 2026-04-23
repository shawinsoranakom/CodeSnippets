def supports_frame_exclusion(self):
        return self.connection.oracle_version >= (21,)