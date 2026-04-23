def options_set(self, field_, value_):
        """
        Set options of the solver.

            :param field: string, e.g. 'print_level', 'rti_phase', 'initialize_t_slacks', 'step_length', 'alpha_min', 'alpha_reduction', 'qp_warm_start', 'line_search_use_sufficient_descent', 'full_step_dual', 'globalization_use_SOC', 'qp_tol_stat', 'qp_tol_eq', 'qp_tol_ineq', 'qp_tol_comp', 'qp_tau_min', 'qp_mu0'

            :param value: of type int, float, string

            - qp_tol_stat: QP solver tolerance stationarity
            - qp_tol_eq: QP solver tolerance equalities
            - qp_tol_ineq: QP solver tolerance inequalities
            - qp_tol_comp: QP solver tolerance complementarity
            - qp_tau_min: for HPIPM QP solvers: minimum value of barrier parameter in HPIPM
            - qp_mu0: for HPIPM QP solvers: initial value for complementarity slackness
            - warm_start_first_qp: indicates if first QP in SQP is warm_started
        """
        int_fields = ['print_level', 'rti_phase', 'initialize_t_slacks', 'qp_warm_start',
                      'line_search_use_sufficient_descent', 'full_step_dual', 'globalization_use_SOC', 'warm_start_first_qp']
        double_fields = ['step_length', 'tol_eq', 'tol_stat', 'tol_ineq', 'tol_comp', 'alpha_min', 'alpha_reduction',
                         'eps_sufficient_descent', 'qp_tol_stat', 'qp_tol_eq', 'qp_tol_ineq', 'qp_tol_comp', 'qp_tau_min', 'qp_mu0']
        string_fields = ['globalization']

        # check field availability and type
        if field_ in int_fields:
            if not isinstance(value_, int):
                raise Exception(f'solver option \'{field_}\' must be of type int. You have {type(value_)}.')
            else:
                value_ctypes = c_int(value_)

        elif field_ in double_fields:
            if not isinstance(value_, float):
                raise Exception(f'solver option \'{field_}\' must be of type float. You have {type(value_)}.')
            else:
                value_ctypes = c_double(value_)

        elif field_ in string_fields:
            if not isinstance(value_, str):
                raise Exception(f'solver option \'{field_}\' must be of type str. You have {type(value_)}.')
            else:
                value_ctypes = value_.encode('utf-8')
        else:
            fields = ', '.join(int_fields + double_fields + string_fields)
            raise Exception(f'AcadosOcpSolver.options_set() does not support field \'{field_}\'.\n'\
                f' Possible values are {fields}.')


        if field_ == 'rti_phase':
            if value_ < 0 or value_ > 2:
                raise Exception('AcadosOcpSolver.options_set(): argument \'rti_phase\' can '
                    'take only values 0, 1, 2 for SQP-RTI-type solvers')
            if self.solver_options['nlp_solver_type'] != 'SQP_RTI' and value_ > 0:
                raise Exception('AcadosOcpSolver.options_set(): argument \'rti_phase\' can '
                    'take only value 0 for SQP-type solvers')

        # encode
        field = field_
        field = field.encode('utf-8')

        # call C interface
        if field_ in string_fields:
            self.shared_lib.ocp_nlp_solver_opts_set.argtypes = \
                [c_void_p, c_void_p, c_char_p, c_char_p]
            self.shared_lib.ocp_nlp_solver_opts_set(self.nlp_config, \
                self.nlp_opts, field, value_ctypes)
        else:
            self.shared_lib.ocp_nlp_solver_opts_set.argtypes = \
                [c_void_p, c_void_p, c_char_p, c_void_p]
            self.shared_lib.ocp_nlp_solver_opts_set(self.nlp_config, \
                self.nlp_opts, field, byref(value_ctypes))
        return