def max_query_params(self):
        if self.uses_server_side_binding:
            return 2**16 - 1
        return None