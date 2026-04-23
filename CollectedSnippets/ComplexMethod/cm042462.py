def print_statistics(self):
        """
        prints statistics of previous solver run as a table:
            - iter: iteration number
            - res_stat: stationarity residual
            - res_eq: residual wrt equality constraints (dynamics)
            - res_ineq: residual wrt inequality constraints (constraints)
            - res_comp: residual wrt complementarity conditions
            - qp_stat: status of QP solver
            - qp_iter: number of QP iterations
            - alpha: SQP step size
            - qp_res_stat: stationarity residual of the last QP solution
            - qp_res_eq: residual wrt equality constraints (dynamics) of the last QP solution
            - qp_res_ineq: residual wrt inequality constraints (constraints)  of the last QP solution
            - qp_res_comp: residual wrt complementarity conditions of the last QP solution
        """
        stat = self.get_stats("statistics")

        if self.solver_options['nlp_solver_type'] == 'SQP':
            print('\niter\tres_stat\tres_eq\t\tres_ineq\tres_comp\tqp_stat\tqp_iter\talpha')
            if stat.shape[0]>8:
                print('\tqp_res_stat\tqp_res_eq\tqp_res_ineq\tqp_res_comp')
            for jj in range(stat.shape[1]):
                print(f'{int(stat[0][jj]):d}\t{stat[1][jj]:e}\t{stat[2][jj]:e}\t{stat[3][jj]:e}\t' +
                      f'{stat[4][jj]:e}\t{int(stat[5][jj]):d}\t{int(stat[6][jj]):d}\t{stat[7][jj]:e}\t')
                if stat.shape[0]>8:
                    print('\t{:e}\t{:e}\t{:e}\t{:e}'.format( \
                        stat[8][jj], stat[9][jj], stat[10][jj], stat[11][jj]))
            print('\n')
        elif self.solver_options['nlp_solver_type'] == 'SQP_RTI':
            print('\niter\tqp_stat\tqp_iter')
            if stat.shape[0]>3:
                print('\tqp_res_stat\tqp_res_eq\tqp_res_ineq\tqp_res_comp')
            for jj in range(stat.shape[1]):
                print('{:d}\t{:d}\t{:d}'.format( int(stat[0][jj]), int(stat[1][jj]), int(stat[2][jj])))
                if stat.shape[0]>3:
                    print('\t{:e}\t{:e}\t{:e}\t{:e}'.format( \
                         stat[3][jj], stat[4][jj], stat[5][jj], stat[6][jj]))
            print('\n')

        return