def build_path_list(route_map: dict[str, BaseRoute]) -> list[str]:
        """Build the path list."""
        path_list = []
        for route_path in route_map:
            if route_path not in path_list:
                path_list.append(route_path)

                sub_path_list = route_path.split("/")

                for length in range(len(sub_path_list)):
                    sub_path = "/".join(sub_path_list[:length])
                    if sub_path not in path_list:
                        # Don't add paths that only exist as part of parameterized routes
                        has_direct_route = sub_path in route_map
                        # A child route is non-parameterized if the next segment doesn't start with {
                        has_real_children = False
                        for r in route_map:
                            if r.startswith(sub_path + "/"):
                                remainder = r[len(sub_path) + 1 :]
                                next_segment = (
                                    remainder.split("/")[0] if remainder else ""
                                )
                                if next_segment and not next_segment.startswith("{"):
                                    has_real_children = True
                                    break

                        if has_direct_route or has_real_children:
                            path_list.append(sub_path)

        return path_list