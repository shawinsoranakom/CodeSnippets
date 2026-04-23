def determine_delta_color_and_direction(
        self,
        delta_color: DeltaColor,
        delta: Delta,
    ) -> MetricColorAndDirection:
        if delta_color not in {"normal", "inverse", "off"}:
            raise StreamlitAPIException(
                f"'{str(delta_color)}' is not an accepted value. delta_color only accepts: "
                "'normal', 'inverse', or 'off'"
            )

        if delta is None or delta == "":
            return MetricColorAndDirection(
                color=MetricProto.MetricColor.GRAY,
                direction=MetricProto.MetricDirection.NONE,
            )

        if self.is_negative(delta):
            if delta_color == "normal":
                cd_color = MetricProto.MetricColor.RED
            elif delta_color == "inverse":
                cd_color = MetricProto.MetricColor.GREEN
            else:
                cd_color = MetricProto.MetricColor.GRAY
            cd_direction = MetricProto.MetricDirection.DOWN
        else:
            if delta_color == "normal":
                cd_color = MetricProto.MetricColor.GREEN
            elif delta_color == "inverse":
                cd_color = MetricProto.MetricColor.RED
            else:
                cd_color = MetricProto.MetricColor.GRAY
            cd_direction = MetricProto.MetricDirection.UP

        return MetricColorAndDirection(
            color=cd_color,
            direction=cd_direction,
        )