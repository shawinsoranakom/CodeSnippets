def test_json_unserializable(self):
        """Test Text.JSON with unserializable object."""
        obj = json  # Modules aren't serializable.

        # Testing unserializable object.
        st.json(obj)

        element = self.get_delta_from_queue().new_element

        # validate a substring since repr for a module may contain an installation-specific path
        self.assertTrue(element.json.body.startswith("\"<module 'json'"))