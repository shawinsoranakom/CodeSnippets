def help(self, obj: Any) -> "DeltaGenerator":
        """Display object's doc string, nicely formatted.

        Displays the doc string for this object.

        Parameters
        ----------
        obj : Object
            The object whose docstring should be displayed.

        Example
        -------

        Don't remember how to initialize a dataframe? Try this:

        >>> st.help(pandas.DataFrame)

        Want to quickly check what datatype is output by a certain function?
        Try:

        >>> x = my_poorly_documented_function()
        >>> st.help(x)

        """
        doc_string_proto = DocStringProto()
        _marshall(doc_string_proto, obj)
        return self.dg._enqueue("doc_string", doc_string_proto)