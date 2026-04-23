def check_output(self, function, value, output=None):
        """
        function(value) equals output. If output is None, function(value)
        equals value.
        """
        if output is None:
            output = value
        self.assertEqual(function(value), output)