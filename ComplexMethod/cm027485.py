def _update_data() -> dict[RouteStop, dict[str, Any]]:
            """Fetch data from NextBus."""
            self.logger.debug("Updating data from API (executor)")
            predictions: dict[RouteStop, dict[str, Any]] = {}

            for stop_id, route_stops in _stops_to_route_stops.items():
                self.logger.debug("Updating data from API (executor) %s", stop_id)
                try:
                    prediction_results = self.client.predictions_for_stop(stop_id)
                except NextBusHTTPError as ex:
                    self.logger.error(
                        "Error updating %s (executor): %s %s",
                        str(stop_id),
                        ex,
                        getattr(ex, "response", None),
                    )
                    raise UpdateFailed("Failed updating nextbus data", ex) from ex
                except NextBusFormatError as ex:
                    raise UpdateFailed("Failed updating nextbus data", ex) from ex

                self.logger.debug(
                    "Prediction results for %s (executor): %s",
                    str(stop_id),
                    str(prediction_results),
                )

                for route_stop in route_stops:
                    for prediction_result in prediction_results:
                        if (
                            prediction_result["stop"]["id"] == route_stop.stop_id
                            and prediction_result["route"]["id"] == route_stop.route_id
                        ):
                            predictions[route_stop] = prediction_result
                            break
                    else:
                        self.logger.warning(
                            "Prediction not found for %s (executor)", str(route_stop)
                        )

            self._predictions = predictions

            return predictions