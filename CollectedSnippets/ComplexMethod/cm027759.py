def copy(self, deep: bool = False) -> Self:
        if deep:
            return self.deepcopy()

        result = copy.copy(self)

        result.parents = []
        result.target = None
        result.saved_state = None

        # copy.copy is only a shallow copy, so the internal
        # data which are numpy arrays or other mobjects still
        # need to be further copied.
        result.uniforms = {
            key: value.copy() if isinstance(value, np.ndarray) else value
            for key, value in self.uniforms.items()
        }

        # Instead of adding using result.add, which does some checks for updating
        # updater statues and bounding box, just directly modify the family-related
        # lists
        result.submobjects = [sm.copy() for sm in self.submobjects]
        for sm in result.submobjects:
            sm.parents = [result]
        result.family = [result, *it.chain(*(sm.get_family() for sm in result.submobjects))]

        # Similarly, instead of calling match_updaters, since we know the status
        # won't have changed, just directly match.
        result.updaters = list(self.updaters)
        result._data_has_changed = True
        result.shader_wrapper = None

        family = self.get_family()
        for attr, value in self.__dict__.items():
            if isinstance(value, Mobject) and value is not self:
                if value in family:
                    setattr(result, attr, result.family[family.index(value)])
            elif isinstance(value, np.ndarray):
                setattr(result, attr, value.copy())
        return result