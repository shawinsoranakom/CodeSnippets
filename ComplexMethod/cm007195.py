async def _build_each_vertex_in_params_dict(self) -> None:
        """Iterates over each vertex in the params dictionary and builds it."""
        for key, value in self.raw_params.items():
            if self._is_vertex(value):
                if value == self:
                    del self.params[key]
                    continue
                await self._build_vertex_and_update_params(
                    key,
                    value,
                )
            elif isinstance(value, list) and self._is_list_of_vertices(value):
                await self._build_list_of_vertices_and_update_params(key, value)
            elif isinstance(value, dict):
                await self._build_dict_and_update_params(
                    key,
                    value,
                )
            elif key not in self.params or self.updated_raw_params:
                self.params[key] = value

        # Reset the flag after processing raw_params
        if self.updated_raw_params:
            self.updated_raw_params = False