def modify_insert_params(self, placeholder, params):
        """
        Allow modification of insert parameters. Needed for Oracle Spatial
        backend due to #10888.
        """
        return params