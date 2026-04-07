def db_type(self, connection):
        """
        Return the database column data type for this field, for the provided
        connection.
        """
        # The default implementation of this method looks at the
        # backend-specific data_types dictionary, looking up the field by its
        # "internal type".
        #
        # A Field class can implement the get_internal_type() method to specify
        # which *preexisting* Django Field class it's most similar to -- i.e.,
        # a custom field might be represented by a TEXT column type, which is
        # the same as the TextField Django field type, which means the custom
        # field's get_internal_type() returns 'TextField'.
        #
        # But the limitation of the get_internal_type() / data_types approach
        # is that it cannot handle database column types that aren't already
        # mapped to one of the built-in Django field types. In this case, you
        # can implement db_type() instead of get_internal_type() to specify
        # exactly which wacky database column type you want to use.
        data = self.db_type_parameters(connection)
        try:
            column_type = connection.data_types[self.get_internal_type()]
        except KeyError:
            return None
        else:
            # column_type is either a single-parameter function or a string.
            if callable(column_type):
                return column_type(data)
            return column_type % data