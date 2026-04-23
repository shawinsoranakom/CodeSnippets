def test_token_request_model_has_api_token_field(self):
        """auth.py TokenRequest should have an api_token field in its source."""
        source = (ROOT / "deploy" / "docker" / "auth.py").read_text()
        # Parse the AST to verify the field exists on the class
        tree = ast.parse(source)
        token_request = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "TokenRequest":
                token_request = node
                break
        assert token_request is not None, "TokenRequest class not found"
        field_names = [
            stmt.target.id
            for stmt in token_request.body
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        ]
        assert "email" in field_names, "TokenRequest missing email field"
        assert "api_token" in field_names, "TokenRequest missing api_token field"