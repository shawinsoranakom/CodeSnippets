def set(self, stage_, field_, value_):
        """
        Set numerical data inside the solver.

            :param stage: integer corresponding to shooting node
            :param field: string in ['x', 'u', 'pi', 'lam', 't', 'p', 'xdot_guess', 'z_guess']

            .. note:: regarding lam, t: \n
                    the inequalities are internally organized in the following order: \n
                    [ lbu lbx lg lh lphi ubu ubx ug uh uphi; \n
                      lsbu lsbx lsg lsh lsphi usbu usbx usg ush usphi]

            .. note:: pi: multipliers for dynamics equality constraints \n
                      lam: multipliers for inequalities \n
                      t: slack variables corresponding to evaluation of all inequalities (at the solution) \n
                      sl: slack variables of soft lower inequality constraints \n
                      su: slack variables of soft upper inequality constraints \n
        """
        cost_fields = ['y_ref', 'yref']
        constraints_fields = ['lbx', 'ubx', 'lbu', 'ubu']
        out_fields = ['x', 'u', 'pi', 'lam', 't', 'z', 'sl', 'su']
        mem_fields = ['xdot_guess', 'z_guess']

        # cast value_ to avoid conversion issues
        if isinstance(value_, (float, int)):
            value_ = np.array([value_])
        value_ = value_.astype(float)

        field = field_.encode('utf-8')

        stage = c_int(stage_)

        # treat parameters separately
        if field_ == 'p':
            getattr(self.shared_lib, f"{self.model_name}_acados_update_params").argtypes = [c_void_p, c_int, POINTER(c_double), c_int]
            getattr(self.shared_lib, f"{self.model_name}_acados_update_params").restype = c_int

            value_data = cast(value_.ctypes.data, POINTER(c_double))

            assert getattr(self.shared_lib, f"{self.model_name}_acados_update_params")(self.capsule, stage, value_data, value_.shape[0])==0
        else:
            if field_ not in constraints_fields + cost_fields + out_fields + mem_fields:
                raise Exception(f"AcadosOcpSolver.set(): '{field}' is not a valid argument.\n"
                    f" Possible values are {constraints_fields + cost_fields + out_fields + mem_fields + ['p']}.")

            self.shared_lib.ocp_nlp_dims_get_from_attr.argtypes = \
                [c_void_p, c_void_p, c_void_p, c_int, c_char_p]
            self.shared_lib.ocp_nlp_dims_get_from_attr.restype = c_int

            dims = self.shared_lib.ocp_nlp_dims_get_from_attr(self.nlp_config, \
                self.nlp_dims, self.nlp_out, stage_, field)

            if value_.shape[0] != dims:
                msg = f'AcadosOcpSolver.set(): mismatching dimension for field "{field_}" '
                msg += f'with dimension {dims} (you have {value_.shape[0]})'
                raise Exception(msg)

            value_data = cast(value_.ctypes.data, POINTER(c_double))
            value_data_p = cast((value_data), c_void_p)

            if field_ in constraints_fields:
                self.shared_lib.ocp_nlp_constraints_model_set.argtypes = \
                    [c_void_p, c_void_p, c_void_p, c_int, c_char_p, c_void_p]
                self.shared_lib.ocp_nlp_constraints_model_set(self.nlp_config, \
                    self.nlp_dims, self.nlp_in, stage, field, value_data_p)
            elif field_ in cost_fields:
                self.shared_lib.ocp_nlp_cost_model_set.argtypes = \
                    [c_void_p, c_void_p, c_void_p, c_int, c_char_p, c_void_p]
                self.shared_lib.ocp_nlp_cost_model_set(self.nlp_config, \
                    self.nlp_dims, self.nlp_in, stage, field, value_data_p)
            elif field_ in out_fields:
                self.shared_lib.ocp_nlp_out_set.argtypes = \
                    [c_void_p, c_void_p, c_void_p, c_int, c_char_p, c_void_p]
                self.shared_lib.ocp_nlp_out_set(self.nlp_config, \
                    self.nlp_dims, self.nlp_out, stage, field, value_data_p)
            elif field_ in mem_fields:
                self.shared_lib.ocp_nlp_set.argtypes = \
                    [c_void_p, c_void_p, c_int, c_char_p, c_void_p]
                self.shared_lib.ocp_nlp_set(self.nlp_config, \
                    self.nlp_solver, stage, field, value_data_p)
            # also set z_guess, when setting z.
            if field_ == 'z':
                field = 'z_guess'.encode('utf-8')
                self.shared_lib.ocp_nlp_set.argtypes = \
                    [c_void_p, c_void_p, c_int, c_char_p, c_void_p]
                self.shared_lib.ocp_nlp_set(self.nlp_config, \
                    self.nlp_solver, stage, field, value_data_p)
        return