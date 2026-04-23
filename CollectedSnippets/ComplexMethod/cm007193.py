def _set_params_from_normal_edge(self, params: dict, edge: Edge, template_dict: dict):
        param_key = edge.target_param

        # If the param_key is in the template_dict and the edge.target_id is the current node
        # We check this to make sure params with the same name but different target_id
        # don't get overwritten
        if param_key in template_dict and edge.target_id == self.id:
            if template_dict[param_key].get("list"):
                if param_key not in params:
                    params[param_key] = []
                params[param_key].append(self.graph.get_vertex(edge.source_id))
            elif edge.target_id == self.id:
                if isinstance(template_dict[param_key].get("value"), dict):
                    # we don't know the key of the dict but we need to set the value
                    # to the vertex that is the source of the edge
                    param_dict = template_dict[param_key]["value"]
                    if not param_dict or len(param_dict) != 1:
                        params[param_key] = self.graph.get_vertex(edge.source_id)
                    else:
                        params[param_key] = {key: self.graph.get_vertex(edge.source_id) for key in param_dict}

                else:
                    params[param_key] = self.graph.get_vertex(edge.source_id)
        elif param_key in self.output_names:
            #  if the loop is run the param_key item will be set over here
            # validate the edge
            params[param_key] = self.graph.get_vertex(edge.source_id)
        return params