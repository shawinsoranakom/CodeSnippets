def test_nested_with(self):
        with st.container():
            with st.container():
                st.markdown("Level 2 with")
                msg = self.get_message_from_queue()
                self.assertEqual(
                    make_delta_path(RootContainer.MAIN, (0, 0), 0),
                    msg.metadata.delta_path,
                )

            st.markdown("Level 1 with")
            msg = self.get_message_from_queue()
            self.assertEqual(
                make_delta_path(RootContainer.MAIN, (0,), 1),
                msg.metadata.delta_path,
            )