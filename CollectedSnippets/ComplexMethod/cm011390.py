def get_mesh_from_args(self, validate: bool = True) -> DeviceMesh:
        """
        This util can be used to get a mesh from the OpSchema that contains multiple
        DTensors as arguments. When `validate` is True, it will try to validate that all the
        arguments have the same mesh to avoid unexpected cross mesh errors.

        NOTE: this util currently does not handle TupleStrategy when `validate=True`,
        this is because for TupleStrategy there could be different types of checks, i.e.:
            - for stack and cat like op, we need to check within a TupleStrategy is every
              input is on the same mesh
            - for foreach like ops we need to check "zipped" inputs are on the same mesh
              for each index.
        """
        mesh = None
        # Scan all args to find the first DTensorSpec/OpStrategy (not just the first arg)
        for arg in self.args_schema:
            if isinstance(arg, (DTensorSpec, OpStrategy)):
                mesh = arg.mesh
                break
            elif isinstance(arg, (list, tuple, TupleStrategy)):
                # Scan all elements in the list/tuple, not just the first one,
                # to handle cases like List[Optional[Tensor]] where first elem may be None
                elems = arg.children if isinstance(arg, TupleStrategy) else arg
                for elem in elems:
                    if isinstance(elem, (DTensorSpec, OpStrategy)):
                        mesh = elem.mesh
                        break
                if mesh is not None:
                    break
        if mesh is None:
            raise ValueError(f"Cannot find device mesh from args for op : {self.op}.")

        if validate:
            for arg in self.args_schema[1:]:
                if isinstance(arg, (DTensorSpec, OpStrategy)) and arg.mesh != mesh:
                    raise RuntimeError(
                        f"DTensor does not support cross-mesh operation on {self.op}! "
                        f"Got meshes: {mesh} {arg.mesh}. "
                        f"Please make sure all the arguments have the same DeviceMesh."
                    )

        return mesh