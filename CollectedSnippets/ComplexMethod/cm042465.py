def get_stats(self, field_):
        """
        Get the information of the last solver call.

            :param field: string in ['statistics', 'time_tot', 'time_lin', 'time_sim', 'time_sim_ad', 'time_sim_la', 'time_qp', 'time_qp_solver_call', 'time_reg', 'sqp_iter', 'residuals', 'qp_iter', 'alpha']

        Available fileds:
            - time_tot: total CPU time previous call
            - time_lin: CPU time for linearization
            - time_sim: CPU time for integrator
            - time_sim_ad: CPU time for integrator contribution of external function calls
            - time_sim_la: CPU time for integrator contribution of linear algebra
            - time_qp: CPU time qp solution
            - time_qp_solver_call: CPU time inside qp solver (without converting the QP)
            - time_qp_xcond: time_glob: CPU time globalization
            - time_solution_sensitivities: CPU time for previous call to eval_param_sens
            - time_reg: CPU time regularization
            - sqp_iter: number of SQP iterations
            - qp_iter: vector of QP iterations for last SQP call
            - statistics: table with info about last iteration
            - stat_m: number of rows in statistics matrix
            - stat_n: number of columns in statistics matrix
            - residuals: residuals of last iterate
            - alpha: step sizes of SQP iterations
        """

        double_fields = ['time_tot',
                  'time_lin',
                  'time_sim',
                  'time_sim_ad',
                  'time_sim_la',
                  'time_qp',
                  'time_qp_solver_call',
                  'time_qp_xcond',
                  'time_glob',
                  'time_solution_sensitivities',
                  'time_reg'
        ]
        fields = double_fields + [
                  'sqp_iter',
                  'qp_iter',
                  'statistics',
                  'stat_m',
                  'stat_n',
                  'residuals',
                  'alpha',
                ]
        field = field_.encode('utf-8')


        if field_ in ['sqp_iter', 'stat_m', 'stat_n']:
            out = np.ascontiguousarray(np.zeros((1,)), dtype=np.int64)
            out_data = cast(out.ctypes.data, POINTER(c_int64))
            self.shared_lib.ocp_nlp_get.argtypes = [c_void_p, c_void_p, c_char_p, c_void_p]
            self.shared_lib.ocp_nlp_get(self.nlp_config, self.nlp_solver, field, out_data)
            return out

        # TODO: just return double instead of np.
        elif field_ in double_fields:
            out = np.zeros((1,))
            out_data = cast(out.ctypes.data, POINTER(c_double))
            self.shared_lib.ocp_nlp_get.argtypes = [c_void_p, c_void_p, c_char_p, c_void_p]
            self.shared_lib.ocp_nlp_get(self.nlp_config, self.nlp_solver, field, out_data)
            return out

        elif field_ == 'statistics':
            sqp_iter = self.get_stats("sqp_iter")
            stat_m = self.get_stats("stat_m")
            stat_n = self.get_stats("stat_n")
            min_size = min([stat_m, sqp_iter+1])
            out = np.ascontiguousarray(
                        np.zeros((stat_n[0]+1, min_size[0])), dtype=np.float64)
            out_data = cast(out.ctypes.data, POINTER(c_double))
            self.shared_lib.ocp_nlp_get.argtypes = [c_void_p, c_void_p, c_char_p, c_void_p]
            self.shared_lib.ocp_nlp_get(self.nlp_config, self.nlp_solver, field, out_data)
            return out

        elif field_ == 'qp_iter':
            full_stats = self.get_stats('statistics')
            if self.solver_options['nlp_solver_type'] == 'SQP':
                return full_stats[6, :]
            elif self.solver_options['nlp_solver_type'] == 'SQP_RTI':
                return full_stats[2, :]

        elif field_ == 'alpha':
            full_stats = self.get_stats('statistics')
            if self.solver_options['nlp_solver_type'] == 'SQP':
                return full_stats[7, :]
            else: # self.solver_options['nlp_solver_type'] == 'SQP_RTI':
                raise Exception("alpha values are not available for SQP_RTI")

        elif field_ == 'residuals':
            return self.get_residuals()

        else:
            raise Exception(f'AcadosOcpSolver.get_stats(): \'{field}\' is not a valid argument.'
                    + f'\n Possible values are {fields}.')