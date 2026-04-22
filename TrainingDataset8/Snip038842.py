def test_use_container_width_true(self):
        """Test that it can be called with use_container_width."""
        graph = graphviz.Graph(comment="The Round Table")
        graph.node("A", "King Arthur")
        graph.node("B", "Sir Bedevere the Wise")
        graph.edges(["AB"])

        st.graphviz_chart(graph, use_container_width=True)

        c = self.get_delta_from_queue().new_element.graphviz_chart
        self.assertEqual(c.use_container_width, True)