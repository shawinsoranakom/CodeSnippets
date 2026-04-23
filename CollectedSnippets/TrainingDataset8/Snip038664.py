def test_container(self):
        container = st.container()

        self.assertIsInstance(container, DeltaGenerator)
        self.assertFalse(container._cursor.is_locked)