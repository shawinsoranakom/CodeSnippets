def handler(self, other, *on, **kwargs):
        processed_kwargs = {}
        if "how" in kwargs:
            how = kwargs.pop("how")
            processed_kwargs["how"] = how
            if not allow_how:
                raise ValueError(
                    "Received `how` argument but was not expecting any.\n"
                    + "Consider using a generic join method that handles `how` "
                    + "to decide on a type of a join to be used."
                )
            elif isinstance(how, JoinMode):
                pass
            elif isinstance(how, str):
                raise ValueError(
                    "Received `how` argument of join that is a string.\n"
                    + "You probably want to use one of "
                    + "JoinMode.INNER, JoinMode.LEFT, JoinMode.RIGHT or JoinMode.OUTER values."
                )
            else:
                raise ValueError(
                    "How argument of join should be one of "
                    + "JoinMode.INNER, JoinMode.LEFT, JoinMode.RIGHT or JoinMode.OUTER values."
                )

        if "id" in kwargs:
            id = kwargs.pop("id")
            processed_kwargs["id"] = id
            if not allow_id:
                raise ValueError(
                    "Received `id` argument but was not expecting any.\n"
                    + "Not every join type supports `id` argument."
                )
            elif id is None:
                pass
            elif isinstance(id, str):
                raise ValueError(
                    "Received `id` argument of join that is a string.\n"
                    + f"Did you mean <table>.{id}"
                    + f" instead of {repr(id)}?"
                )
            elif not isinstance(id, expr.ColumnReference):
                raise ValueError(
                    "The id argument of a join has to be a ColumnReference."
                )

        if "defaults" in kwargs:
            processed_kwargs["defaults"] = kwargs.pop("defaults")

        if "left_instance" in kwargs and "right_instance" in kwargs:
            processed_kwargs["left_instance"] = kwargs.pop("left_instance")
            processed_kwargs["right_instance"] = kwargs.pop("right_instance")
        elif "left_instance" in kwargs or "right_instance" in kwargs:
            raise ValueError(
                "`left_instance` and `right_instance` arguments to join "
                + "should always be provided simultaneously"
            )

        if "direction" in kwargs:
            direction = processed_kwargs["direction"] = kwargs.pop("direction")
            from pathway.stdlib.temporal import Direction

            if isinstance(direction, str):
                raise ValueError(
                    "Received `direction` argument of join that is a string.\n"
                    + "You probably want to use one of "
                    + "Direction.BACKWARD, Direction.FORWARD or Direction.NEAREST values."
                )
            if not isinstance(direction, Direction):
                raise ValueError(
                    "direction argument of join should be of type asof_join.Direction."
                )

        if "behavior" in kwargs:
            behavior = processed_kwargs["behavior"] = kwargs.pop("behavior")
            from pathway.stdlib.temporal import CommonBehavior

            if not isinstance(behavior, CommonBehavior):
                raise ValueError(
                    "The behavior argument of join should be of type pathway.temporal.CommonBehavior."
                )

        if "interval" in kwargs:
            from pathway.stdlib.temporal import Interval

            interval = processed_kwargs["interval"] = kwargs.pop("interval")
            if not isinstance(interval, Interval):
                raise ValueError(
                    "The interval argument of a join should be of a type pathway.temporal.Interval."
                )

        if "left_exactly_once" in kwargs:
            processed_kwargs["left_exactly_once"] = kwargs.pop("left_exactly_once")

        if "right_exactly_once" in kwargs:
            processed_kwargs["right_exactly_once"] = kwargs.pop("right_exactly_once")

        if kwargs:
            raise ValueError(
                "Join received extra kwargs.\n"
                + "You probably want to use TableLike.join(...).select(**kwargs) to compute output columns."
            )
        return (self, other, *on), processed_kwargs