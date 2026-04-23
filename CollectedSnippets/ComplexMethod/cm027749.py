def __init__(
        self,
        *args: AnimationType | Iterable[AnimationType],
        run_time: float = -1,  # If negative, default to sum of inputed animation runtimes
        lag_ratio: float = 0.0,
        group: Optional[Mobject] = None,
        group_type: Optional[type] = None,
        **kwargs
    ):
        animations = args[0] if isinstance(args[0], Iterable) else args
        self.animations = [prepare_animation(anim) for anim in animations]
        self.build_animations_with_timings(lag_ratio)
        self.max_end_time = max((awt[2] for awt in self.anims_with_timings), default=0)
        self.run_time = self.max_end_time if run_time < 0 else run_time
        self.lag_ratio = lag_ratio
        mobs = remove_list_redundancies([a.mobject for a in self.animations])
        if group is not None:
            self.group = group
        elif group_type is not None:
            self.group = group_type(*mobs)
        elif all(isinstance(anim.mobject, VMobject) for anim in animations):
            self.group = VGroup(*mobs)
        else:
            self.group = Group(*mobs)

        super().__init__(
            self.group,
            run_time=self.run_time,
            lag_ratio=lag_ratio,
            **kwargs
        )