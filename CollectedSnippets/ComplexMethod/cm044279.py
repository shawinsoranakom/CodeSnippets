def get_path_hint_type_list(cls, path: str) -> list[type]:
        """Get the hint type list from the path."""
        route_map = PathHandler.build_route_map()
        path_list = PathHandler.build_path_list(route_map=route_map)
        child_path_list = PathHandler.get_child_path_list(
            path=path, path_list=path_list
        )
        hint_type_list = []
        for child_path in child_path_list:
            route = PathHandler.get_route(path=child_path, route_map=route_map)
            if route:
                if getattr(route, "deprecated", None):
                    hint_type_list.append(type(route.summary.metadata))  # type: ignore
                function_hint_type_list = cls.get_function_hint_type_list(route=route)  # type: ignore
                hint_type_list.extend(function_hint_type_list)

        for dependency in PathHandler.get_router_dependencies(path):
            dependency_func = getattr(dependency, "dependency", None)
            if callable(dependency_func):
                hint_type_list.append(dependency_func)

        hint_type_list = [
            d
            for d in list(set(hint_type_list))
            if d not in [int, list, str, dict, float, set, bool, tuple]
        ]
        return hint_type_list