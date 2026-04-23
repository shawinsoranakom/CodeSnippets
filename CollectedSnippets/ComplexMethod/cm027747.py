def add_transform(
        self,
        source: Mobject,
        target: Mobject,
    ):
        new_source_pieces = source.family_members_with_points()
        new_target_pieces = target.family_members_with_points()
        if len(new_source_pieces) == 0 or len(new_target_pieces) == 0:
            # Don't animate null sorces or null targets
            return
        source_is_new = all(char in self.source_pieces for char in new_source_pieces)
        target_is_new = all(char in self.target_pieces for char in new_target_pieces)
        if not source_is_new or not target_is_new:
            return

        transform_type = self.mismatch_animation
        if source.has_same_shape_as(target):
            transform_type = self.match_animation

        self.anims.append(transform_type(source, target, **self.anim_config))
        for char in new_source_pieces:
            self.source_pieces.remove(char)
        for char in new_target_pieces:
            self.target_pieces.remove(char)