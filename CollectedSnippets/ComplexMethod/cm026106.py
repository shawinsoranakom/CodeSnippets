async def async_get_travel_times(
    client: WazeRouteCalculator,
    origin: str,
    destination: str,
    vehicle_type: str,
    avoid_toll_roads: bool,
    avoid_subscription_roads: bool,
    avoid_ferries: bool,
    realtime: bool,
    units: Literal["metric", "imperial"] = "metric",
    incl_filters: Collection[str] | None = None,
    excl_filters: Collection[str] | None = None,
    time_delta: int = 0,
    base_coordinates: tuple[float, float] | None = None,
) -> list[CalcRoutesResponse]:
    """Get all available routes."""

    incl_filters = incl_filters or ()
    excl_filters = excl_filters or ()

    _LOGGER.debug(
        "Getting update for origin: %s destination: %s",
        origin,
        destination,
    )
    routes = []
    vehicle_type = "" if vehicle_type.upper() == "CAR" else vehicle_type.upper()
    try:
        routes = await client.calc_routes(
            origin,
            destination,
            vehicle_type=vehicle_type,
            avoid_toll_roads=avoid_toll_roads,
            avoid_subscription_roads=avoid_subscription_roads,
            avoid_ferries=avoid_ferries,
            real_time=realtime,
            alternatives=3,
            time_delta=time_delta,
            base_coords=base_coordinates,
        )

        if len(routes) < 1:
            _LOGGER.warning("No routes found")
            return routes

        _LOGGER.debug("Got routes: %s", routes)

        incl_routes: list[CalcRoutesResponse] = []

        def should_include_route(route: CalcRoutesResponse) -> bool:
            if len(incl_filters) < 1:
                return True
            should_include = any(
                street_name in incl_filters or "" in incl_filters
                for street_name in route.street_names
            )
            if not should_include:
                _LOGGER.debug(
                    "Excluding route [%s], because no inclusive filter matched any streetname",
                    route.name,
                )
                return False
            return True

        incl_routes = [route for route in routes if should_include_route(route)]

        filtered_routes: list[CalcRoutesResponse] = []

        def should_exclude_route(route: CalcRoutesResponse) -> bool:
            for street_name in route.street_names:
                for excl_filter in excl_filters:
                    if excl_filter == street_name:
                        _LOGGER.debug(
                            "Excluding route, because exclusive filter [%s] matched streetname: %s",
                            excl_filter,
                            route.name,
                        )
                        return True
            return False

        filtered_routes = [
            route for route in incl_routes if not should_exclude_route(route)
        ]

        if len(filtered_routes) < 1:
            _LOGGER.warning("No routes matched your filters")
            return filtered_routes

        if units == IMPERIAL_UNITS:
            filtered_routes = [
                CalcRoutesResponse(
                    name=route.name,
                    distance=DistanceConverter.convert(
                        route.distance, UnitOfLength.KILOMETERS, UnitOfLength.MILES
                    ),
                    duration=route.duration,
                    street_names=route.street_names,
                )
                for route in filtered_routes
                if route.distance is not None
            ]

    except WRCError as exp:
        raise UpdateFailed(f"Error on retrieving data: {exp}") from exp

    else:
        return filtered_routes