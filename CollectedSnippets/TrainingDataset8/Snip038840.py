def test_spec(self):
        """Test that it can be called with spec."""
        graph = graphviz.Graph(comment="The Round Table")
        graph.node("A", "King Arthur")
        graph.node("B", "Sir Bedevere the Wise")
        graph.edges(["AB"])

        st.graphviz_chart(graph)

        c = self.get_delta_from_queue().new_element.graphviz_chart
        self.assertEqual(hasattr(c, "spec"), True)