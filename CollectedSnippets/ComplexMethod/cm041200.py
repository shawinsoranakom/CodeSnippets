def matches(self, query_args: MultiDict, headers: Headers) -> bool:
        """
        Returns true if the given query args and the given headers of a request match the required query args and
        headers of this rule.
        :param query_args: query arguments of the incoming request
        :param headers: headers of the incoming request
        :return: True if the query args and headers match the required args of this rule
        """
        if self.required_query_args:
            for key, values in self.required_query_args.items():
                if key not in query_args:
                    return False
                # if a required query arg also has a list of required values set, the values need to match as well
                if values:
                    query_arg_values = query_args.getlist(key)
                    for value in values:
                        if value not in query_arg_values:
                            return False

        if self.required_header_args:
            for key in self.required_header_args:
                if key not in headers:
                    return False

        return True