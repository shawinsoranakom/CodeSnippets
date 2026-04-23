def __init__(
        self,
        source: Mobject,
        target: Mobject,
        matched_pairs: Iterable[tuple[Mobject, Mobject]] = [],
        match_animation: type = Transform,
        mismatch_animation: type = Transform,
        run_time: float = 2,
        lag_ratio: float = 0,
        **kwargs,
    ):
        self.source = source
        self.target = target
        self.match_animation = match_animation
        self.mismatch_animation = mismatch_animation
        self.anim_config = dict(**kwargs)

        # We will progressively build up a list of transforms
        # from pieces in source to those in target. These
        # two lists keep track of which pieces are accounted
        # for so far
        self.source_pieces = source.family_members_with_points()
        self.target_pieces = target.family_members_with_points()
        self.anims = []

        for pair in matched_pairs:
            self.add_transform(*pair)

        # Match any pairs with the same shape
        for pair in self.find_pairs_with_matching_shapes(self.source_pieces, self.target_pieces):
            self.add_transform(*pair)

        # Finally, account for mismatches
        for source_piece in self.source_pieces:
            if any([source_piece in anim.mobject.get_family() for anim in self.anims]):
                continue
            self.anims.append(FadeOutToPoint(
                source_piece, target.get_center(),
                **self.anim_config
            ))
        for target_piece in self.target_pieces:
            if any([target_piece in anim.mobject.get_family() for anim in self.anims]):
                continue
            self.anims.append(FadeInFromPoint(
                target_piece, source.get_center(),
                **self.anim_config
            ))

        super().__init__(
            *self.anims,
            run_time=run_time,
            lag_ratio=lag_ratio,
        )