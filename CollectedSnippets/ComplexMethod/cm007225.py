def dump(
        self, name: str | None = None, description: str | None = None, endpoint_name: str | None = None
    ) -> GraphDump:
        if self.raw_graph_data != {"nodes": [], "edges": []}:
            data_dict = self.raw_graph_data
        else:
            # we need to convert the vertices and edges to json
            nodes = [node.to_data() for node in self.vertices]
            edges = [edge.to_data() for edge in self.edges]
            self.raw_graph_data = {"nodes": nodes, "edges": edges}
            data_dict = self.raw_graph_data
        graph_dict: GraphDump = {
            "data": data_dict,
            "is_component": len(data_dict.get("nodes", [])) == 1 and data_dict["edges"] == [],
        }
        if name:
            graph_dict["name"] = name
        elif name is None and self.flow_name:
            graph_dict["name"] = self.flow_name
        if description:
            graph_dict["description"] = description
        elif description is None and self.description:
            graph_dict["description"] = self.description
        graph_dict["endpoint_name"] = str(endpoint_name)
        return graph_dict