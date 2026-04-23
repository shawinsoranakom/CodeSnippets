def test_with(self):
        # Same as test_container_paths, but using `with` syntax
        level3 = st.container().container().container()
        with level3:
            st.markdown("hi")
            st.markdown("bye")

        msg = self.get_message_from_queue()
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (0, 0, 0), 1), msg.metadata.delta_path
        )

        # Now we're out of the `with` block, commands should use the main dg
        st.markdown("outside")

        msg = self.get_message_from_queue()
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 1), msg.metadata.delta_path
        )