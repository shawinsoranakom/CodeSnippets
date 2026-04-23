def test_deserializer_pyyaml_error_message(self):
        """Using yaml deserializer without pyyaml raises ImportError"""
        with self.assertRaises(ImportError):
            serializers.deserialize("yaml", "")