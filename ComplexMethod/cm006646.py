def test_simple_agent_flow_loads_directly(self, simple_agent_flow_path: Path):
        """Test that Simple Agent flow loads correctly using load_flow_from_json."""
        from lfx.load import load_flow_from_json

        try:
            graph = load_flow_from_json(simple_agent_flow_path, disable_logs=True)
            assert graph is not None, "Graph should not be None"
            assert hasattr(graph, "vertices"), "Graph should have vertices"
            assert len(graph.vertices) > 0, "Graph should have at least one vertex"

            # Prepare the graph
            graph.prepare()

            # Verify Agent component is in the graph
            component_types = {v.display_name for v in graph.vertices if hasattr(v, "display_name")}
            assert "Agent" in component_types or any("Agent" in ct for ct in component_types), (
                f"Expected Agent in graph, found: {component_types}"
            )

        except ModuleNotFoundError as e:
            pytest.fail(f"ModuleNotFoundError loading graph: {e}")
        except Exception as e:
            if "resolve_component_path" in str(e):
                pytest.fail(f"Storage service error: {e}")
            raise