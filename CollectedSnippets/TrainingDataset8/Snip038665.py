def test_container_paths(self):
        level3 = st.container().container().container()
        level3.markdown("hi")
        level3.markdown("bye")

        msg = self.get_message_from_queue()
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (0, 0, 0), 1), msg.metadata.delta_path
        )