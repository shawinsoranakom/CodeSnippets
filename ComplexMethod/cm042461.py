def get(self, stage_, field_):
        """
        Get the last solution of the solver:

            :param stage: integer corresponding to shooting node
            :param field: string in ['x', 'u', 'z', 'pi', 'lam', 't', 'sl', 'su',]

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

        out_fields = ['x', 'u', 'z', 'pi', 'lam', 't', 'sl', 'su']
        # mem_fields = ['sl', 'su']
        sens_fields = ['sens_u', "sens_x"]
        all_fields = out_fields + sens_fields

        field = field_

        if (field_ not in all_fields):
            raise Exception(f'AcadosOcpSolver.get(stage={stage_}, field={field_}): \'{field_}\' is an invalid argument.\
                    \n Possible values are {all_fields}.')

        if not isinstance(stage_, int):
            raise Exception(f'AcadosOcpSolver.get(stage={stage_}, field={field_}): stage index must be an integer, got type {type(stage_)}.')

        if stage_ < 0 or stage_ > self.N:
            raise Exception(f'AcadosOcpSolver.get(stage={stage_}, field={field_}): stage index must be in [0, {self.N}], got: {stage_}.')

        if stage_ == self.N and field_ == 'pi':
            raise Exception(f'AcadosOcpSolver.get(stage={stage_}, field={field_}): field \'{field_}\' does not exist at final stage {stage_}.')

        if field_ in sens_fields:
            field = field_.replace('sens_', '')

        field = field.encode('utf-8')

        self.shared_lib.ocp_nlp_dims_get_from_attr.argtypes = \
            [c_void_p, c_void_p, c_void_p, c_int, c_char_p]
        self.shared_lib.ocp_nlp_dims_get_from_attr.restype = c_int

        dims = self.shared_lib.ocp_nlp_dims_get_from_attr(self.nlp_config, \
            self.nlp_dims, self.nlp_out, stage_, field)

        out = np.ascontiguousarray(np.zeros((dims,)), dtype=np.float64)
        out_data = cast(out.ctypes.data, POINTER(c_double))

        if (field_ in out_fields):
            self.shared_lib.ocp_nlp_out_get.argtypes = \
                [c_void_p, c_void_p, c_void_p, c_int, c_char_p, c_void_p]
            self.shared_lib.ocp_nlp_out_get(self.nlp_config, \
                self.nlp_dims, self.nlp_out, stage_, field, out_data)
        # elif field_ in mem_fields:
        #     self.shared_lib.ocp_nlp_get_at_stage.argtypes = \
        #         [c_void_p, c_void_p, c_void_p, c_int, c_char_p, c_void_p]
        #     self.shared_lib.ocp_nlp_get_at_stage(self.nlp_config, \
        #         self.nlp_dims, self.nlp_solver, stage_, field, out_data)
        elif field_ in sens_fields:
            self.shared_lib.ocp_nlp_out_get.argtypes = \
                [c_void_p, c_void_p, c_void_p, c_int, c_char_p, c_void_p]
            self.shared_lib.ocp_nlp_out_get(self.nlp_config, \
                self.nlp_dims, self.sens_out, stage_, field, out_data)

        return out