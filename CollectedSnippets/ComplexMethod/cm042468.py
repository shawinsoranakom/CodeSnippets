def constraints_set(self, stage_, field_, value_, api='warn'):
        """
        Set numerical data in the constraint module of the solver.

            :param stage: integer corresponding to shooting node
            :param field: string in ['lbx', 'ubx', 'lbu', 'ubu', 'lg', 'ug', 'lh', 'uh', 'uphi', 'C', 'D']
            :param value: of appropriate size
        """
        # cast value_ to avoid conversion issues
        if isinstance(value_, (float, int)):
            value_ = np.array([value_])
        value_ = value_.astype(float)

        field = field_
        field = field.encode('utf-8')

        stage = c_int(stage_)
        self.shared_lib.ocp_nlp_constraint_dims_get_from_attr.argtypes = \
            [c_void_p, c_void_p, c_void_p, c_int, c_char_p, POINTER(c_int)]
        self.shared_lib.ocp_nlp_constraint_dims_get_from_attr.restype = c_int

        dims = np.ascontiguousarray(np.zeros((2,)), dtype=np.intc)
        dims_data = cast(dims.ctypes.data, POINTER(c_int))

        self.shared_lib.ocp_nlp_constraint_dims_get_from_attr(self.nlp_config, \
            self.nlp_dims, self.nlp_out, stage_, field, dims_data)

        value_shape = value_.shape
        if len(value_shape) == 1:
            value_shape = (value_shape[0], 0)
        elif len(value_shape) == 2:
            if api=='old':
                pass
            elif api=='warn':
                if not np.all(np.ravel(value_, order='F')==np.ravel(value_, order='K')):
                    raise Exception("Ambiguity in API detected.\n"
                                    "Are you making an acados model from scrach? Add api='new' to constraints_set and carry on.\n"
                                    "Are you seeing this error suddenly in previously running code? Read on.\n"
                                    f"  You are relying on a now-fixed bug in constraints_set for field '{field}'.\n" +
                                    "  acados_template now correctly passes on any matrices to acados in column major format.\n" +
                                    "  Two options to fix this error: \n" +
                                    "   * Add api='old' to constraints_set to restore old incorrect behaviour\n" +
                                    "   * Add api='new' to constraints_set and remove any unnatural manipulation of the value argument " +
                                    "such as non-mathematical transposes, reshaping, casting to fortran order, etc... " +
                                    "If there is no such manipulation, then you have probably been getting an incorrect solution before.")
                # Get elements in column major order
                value_ = np.ravel(value_, order='F')
            elif api=='new':
                # Get elements in column major order
                value_ = np.ravel(value_, order='F')
            else:
                raise Exception(f"Unknown api: '{api}'")

        if value_shape != tuple(dims):
            raise Exception(f'AcadosOcpSolver.constraints_set(): mismatching dimension' +
                f' for field "{field_}" at stage {stage} with dimension {tuple(dims)} (you have {value_shape})')

        value_data = cast(value_.ctypes.data, POINTER(c_double))
        value_data_p = cast((value_data), c_void_p)

        self.shared_lib.ocp_nlp_constraints_model_set.argtypes = \
            [c_void_p, c_void_p, c_void_p, c_int, c_char_p, c_void_p]
        self.shared_lib.ocp_nlp_constraints_model_set(self.nlp_config, \
            self.nlp_dims, self.nlp_in, stage, field, value_data_p)

        return