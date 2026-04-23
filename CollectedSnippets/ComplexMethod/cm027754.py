def add(self, *mobjects: Mobject, set_depth_test: bool = True, perp_stroke: bool = True):
        for mob in mobjects:
            if set_depth_test and not mob.is_fixed_in_frame() and self.always_depth_test:
                mob.apply_depth_test()
            if isinstance(mob, VMobject) and mob.has_stroke() and perp_stroke:
                mob.set_flat_stroke(False)
        super().add(*mobjects)