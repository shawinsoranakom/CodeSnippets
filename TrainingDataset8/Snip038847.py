def test_st_cache(self):
        """Test st.cache function (since it's from the 'caching' module)."""
        st.help(st.cache)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual("cache", ds.name)
        self.assertEqual("streamlit", ds.module)
        self.assertEqual("<class 'function'>", ds.type)

        if sys.version_info < (3, 9):
            # Optionals are printed as Unions in Python < 3.9
            self.assertEqual(
                ds.signature,
                (
                    "(func: Union[~F, NoneType] = None, "
                    "persist: bool = False, "
                    "allow_output_mutation: bool = False, "
                    "show_spinner: bool = True, "
                    "suppress_st_warning: bool = False, "
                    "hash_funcs: Union[Dict[Union[str, Type[Any]], Callable[[Any], Any]], NoneType] = None, "
                    "max_entries: Union[int, NoneType] = None, "
                    "ttl: Union[float, NoneType] = None"
                    ") -> Union[Callable[[~F], ~F], ~F]"
                ),
            )
        else:
            self.assertEqual(
                ds.signature,
                (
                    "(func: Optional[~F] = None, "
                    "persist: bool = False, "
                    "allow_output_mutation: bool = False, "
                    "show_spinner: bool = True, "
                    "suppress_st_warning: bool = False, "
                    "hash_funcs: Optional[Dict[Union[str, Type[Any]], Callable[[Any], Any]]] = None, "
                    "max_entries: Optional[int] = None, "
                    "ttl: Optional[float] = None"
                    ") -> Union[Callable[[~F], ~F], ~F]"
                ),
            )
        self.assertTrue(ds.doc_string.startswith("Function decorator to"))