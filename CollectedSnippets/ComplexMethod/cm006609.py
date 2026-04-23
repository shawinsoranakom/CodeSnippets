def test_build_component_metadata_with_real_component(self):
        """Test dependency analysis with a real component."""
        from lfx.custom.custom_component.component import Component
        from lfx.custom.utils import build_component_metadata

        # Setup mock frontend node
        mock_frontend = Mock()
        mock_frontend.metadata = {}

        # Use real component code based on LMStudio component
        real_component_code = """from typing import Any
from urllib.parse import urljoin

import httpx
from langchain_openai import ChatOpenAI

from langflow.base.models.model import LCModelComponent
from langflow.field_typing import LanguageModel

class LMStudioModelComponent(LCModelComponent):
    display_name = "LM Studio"
    description = "Generate text using LM Studio Local LLMs."
    icon = "LMStudio"
    name = "LMStudioModel"

    def build(self):
        return {"test": "value"}
"""

        # Create test component
        test_component = Mock(spec=Component)
        test_component._code = real_component_code

        # Call the function
        build_component_metadata(
            mock_frontend, test_component, "langflow.components.lmstudio", "LMStudioModelComponent"
        )

        # Verify metadata was added
        assert "module" in mock_frontend.metadata
        assert "code_hash" in mock_frontend.metadata
        assert "dependencies" in mock_frontend.metadata

        # Verify dependency analysis results
        dep_info = mock_frontend.metadata["dependencies"]
        assert dep_info["total_dependencies"] > 0

        # Check that external dependencies are found (stdlib filtered out)
        package_names = [pkg["name"] for pkg in dep_info["dependencies"]]

        # External packages should be found
        assert "httpx" in package_names  # external
        assert "langchain_openai" in package_names  # external
        assert "langflow" in package_names  # project dependency

        # Stdlib imports should be filtered out
        assert "typing" not in package_names
        assert "urllib" not in package_names
        mock_frontend.outputs = []
        mock_frontend.to_dict = Mock(return_value={"test": "data"})
        mock_frontend.validate_component = Mock()
        mock_frontend.set_base_classes_from_outputs = Mock()
        mock_frontend.display_name = "My Test Component"

        # Create test component
        test_component = Mock(spec=Component)
        test_component.__class__.__name__ = "TestComponent"
        test_component._code = "class TestComponent: pass"
        test_component.template_config = {"inputs": []}

        # Mock get_component_instance to return a mock instance
        with patch("lfx.custom.utils.get_component_instance") as mock_get_instance:
            mock_instance = Mock()
            mock_instance.get_template_config = Mock(return_value={})
            mock_instance._get_field_order = Mock(return_value=[])
            mock_get_instance.return_value = mock_instance

            # Mock add_code_field to return the frontend node
            with (
                patch("lfx.custom.utils.add_code_field", return_value=mock_frontend),
                patch("lfx.custom.utils.reorder_fields"),
            ):
                # Call the function without module_name
                _, _ = build_custom_component_template_from_inputs(test_component, module_name=None)