def test_clear_one_disk_cache(self, mock_os_remove: Mock, mock_open: Mock):
        """A memoized function's clear_cache() property should just clear
        that function's cache."""

        @st.experimental_memo(persist="disk")
        def foo(val):
            return "actual_value"

        foo(0)
        foo(1)

        # We should've opened two files, one for each distinct "foo" call.
        self.assertEqual(2, mock_open.call_count)

        # Get the names of the two files that were created. These will look
        # something like '/mock/home/folder/.streamlit/cache/[long_hash].memo'
        created_filenames = {
            mock_open.call_args_list[0][0][0],
            mock_open.call_args_list[1][0][0],
        }

        mock_os_remove.assert_not_called()

        # Clear foo's cache
        foo.clear()

        # os.remove should have been called once for each of our created cache files
        self.assertEqual(2, mock_os_remove.call_count)

        removed_filenames = {
            mock_os_remove.call_args_list[0][0][0],
            mock_os_remove.call_args_list[1][0][0],
        }

        # The two files we removed should be the same two files we created.
        self.assertEqual(created_filenames, removed_filenames)