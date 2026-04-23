def get_built_result(self):
        # If the Vertex.type is a power component
        # then we need to return the built object
        # instead of the result dict
        if self.is_interface_component and not isinstance(self.built_object, UnbuiltObject):
            result = self.built_object
            # if it is not a dict or a string and hasattr model_dump then
            # return the model_dump
            if not isinstance(result, dict | str) and hasattr(result, "content"):
                return result.content
            return result
        if isinstance(self.built_object, str):
            self.built_result = self.built_object

        if isinstance(self.built_result, UnbuiltResult):
            return {}

        return self.built_result if isinstance(self.built_result, dict) else {"result": self.built_result}