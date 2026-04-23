def test_serializer_pyyaml_error_message(self):
        """Using yaml serializer without pyyaml raises ImportError"""
        jane = Author(name="Jane")
        with self.assertRaises(ImportError):
            serializers.serialize("yaml", [jane])