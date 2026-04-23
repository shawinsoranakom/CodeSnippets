def get_child_path_list(path: str, path_list: list[str]) -> list[str]:
        """Get the child path list.

        This returns both sub-router paths AND direct route paths that are children of the given path.
        For example, for path="/empty", it returns both:
        - "/empty/sub_router" (a sub-router in path_list)
        - "/empty/also_empty/{param}" (a direct route from route_map)
        """
        direct_children = []
        base_depth = path.count("/") if path else 0

        # Get route_map to check for routes that aren't in path_list
        route_map = PathHandler.build_route_map()

        # First, add children from path_list (these are sub-routers)
        for p in path_list:
            if p.startswith(path + "/") if path else p.startswith("/"):
                p_depth = p.count("/")
                if p_depth == base_depth + 1:
                    direct_children.append(p)

        # Second, add routes from route_map that are direct children but not in path_list
        # (these are endpoints with path parameters)
        for route_path in route_map:
            if route_path not in direct_children and (
                route_path.startswith(path + "/")
                if path
                else route_path.startswith("/")
            ):
                # Remove the parent path prefix
                remainder = route_path[len(path) + 1 :] if path else route_path[1:]

                # Split by "/" and count non-empty segments
                segments = [s for s in remainder.split("/") if s]
                if segments:
                    first_non_param_idx = next(
                        (
                            i
                            for i, seg in enumerate(segments)
                            if not seg.startswith("{")
                        ),
                        None,
                    )
                    is_direct_child = first_non_param_idx is None or (
                        first_non_param_idx == 0
                        and all(seg.startswith("{") for seg in segments[1:])
                    )
                    if is_direct_child and route_path not in direct_children:
                        direct_children.append(route_path)

        return direct_children