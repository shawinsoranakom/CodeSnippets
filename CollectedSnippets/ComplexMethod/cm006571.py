def test_type_aliases_import(self):
        """Test that type aliases are accessible."""
        from lfx.field_typing import (
            Callable,
            Code,
            LanguageModel,
            NestedDict,
            Object,
            Retriever,
            Text,
        )

        assert Callable is not None
        assert Code is not None
        assert LanguageModel is not None
        assert NestedDict is not None
        assert Object is not None
        assert Retriever is not None
        assert Text is not None