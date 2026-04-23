def test_analyze_dependencies_basic(self):
        """Test basic dependency analysis."""
        from lfx.custom.dependency_analyzer import analyze_dependencies

        code = """
import os
import sys
from typing import List
import numpy as np
from requests import get
"""

        deps = analyze_dependencies(code, resolve_versions=False)

        # Should find external dependencies only (stdlib imports filtered out)
        assert len(deps) == 2

        # Check external dependencies
        dep_names = [d["name"] for d in deps]
        assert "numpy" in dep_names
        assert "requests" in dep_names

        # Stdlib imports should be filtered out
        assert "os" not in dep_names
        assert "sys" not in dep_names
        assert "typing" not in dep_names