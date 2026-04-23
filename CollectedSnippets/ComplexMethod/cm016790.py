def ux_friendly_pick_node(self, node_list):
        # If an output node is available, do that first.
        # Technically this has no effect on the overall length of execution, but it feels better as a user
        # for a PreviewImage to display a result as soon as it can
        # Some other heuristics could probably be used here to improve the UX further.
        def is_output(node_id):
            class_type = self.dynprompt.get_node(node_id)["class_type"]
            class_def = nodes.NODE_CLASS_MAPPINGS[class_type]
            if hasattr(class_def, 'OUTPUT_NODE') and class_def.OUTPUT_NODE == True:
                return True
            return False

        # If an available node is async, do that first.
        # This will execute the asynchronous function earlier, reducing the overall time.
        def is_async(node_id):
            class_type = self.dynprompt.get_node(node_id)["class_type"]
            class_def = nodes.NODE_CLASS_MAPPINGS[class_type]
            return inspect.iscoroutinefunction(getattr(class_def, class_def.FUNCTION))

        for node_id in node_list:
            if is_output(node_id) or is_async(node_id):
                return node_id

        #This should handle the VAEDecode -> preview case
        for node_id in node_list:
            for blocked_node_id in self.blocking[node_id]:
                if is_output(blocked_node_id):
                    return node_id

        #This should handle the VAELoader -> VAEDecode -> preview case
        for node_id in node_list:
            for blocked_node_id in self.blocking[node_id]:
                for blocked_node_id1 in self.blocking[blocked_node_id]:
                    if is_output(blocked_node_id1):
                        return node_id

        #TODO: this function should be improved
        return node_list[0]