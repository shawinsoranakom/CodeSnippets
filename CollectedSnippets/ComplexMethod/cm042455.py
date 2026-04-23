def generate_c_code_constraint( model, con_name, is_terminal, opts ):

    casadi_codegen_opts = dict(mex=False, casadi_int='int', casadi_real='double')

    # load constraint variables and expression
    x = model.x
    p = model.p

    symbol = get_casadi_symbol(x)

    if is_terminal:
        con_h_expr = model.con_h_expr_e
        con_phi_expr = model.con_phi_expr_e
        # create dummy u, z
        u = symbol('u', 0, 0)
        z = symbol('z', 0, 0)
    else:
        con_h_expr = model.con_h_expr
        con_phi_expr = model.con_phi_expr
        u = model.u
        z = model.z

    if (not is_empty(con_h_expr)) and (not is_empty(con_phi_expr)):
        raise Exception("acados: you can either have constraint_h, or constraint_phi, not both.")

    if (is_empty(con_h_expr) and is_empty(con_phi_expr)):
        # both empty -> nothing to generate
        return

    if is_empty(con_h_expr):
        constr_type = 'BGP'
    else:
        constr_type = 'BGH'

    if is_empty(p):
        p = symbol('p', 0, 0)

    if is_empty(z):
        z = symbol('z', 0, 0)

    if not (is_empty(con_h_expr)) and opts['generate_hess']:
        # multipliers for hessian
        nh = casadi_length(con_h_expr)
        lam_h = symbol('lam_h', nh, 1)

    # set up & change directory
    cwd = os.getcwd()
    constraints_dir = os.path.abspath(os.path.join(opts["code_export_directory"], f'{model.name}_constraints'))
    if not os.path.exists(constraints_dir):
        os.makedirs(constraints_dir)
    os.chdir(constraints_dir)

    # export casadi functions
    if constr_type == 'BGH':
        if is_terminal:
            fun_name = con_name + '_constr_h_e_fun_jac_uxt_zt'
        else:
            fun_name = con_name + '_constr_h_fun_jac_uxt_zt'

        jac_ux_t = ca.transpose(ca.jacobian(con_h_expr, ca.vertcat(u,x)))
        jac_z_t = ca.jacobian(con_h_expr, z)
        constraint_fun_jac_tran = ca.Function(fun_name, [x, u, z, p], \
                [con_h_expr, jac_ux_t, jac_z_t])

        constraint_fun_jac_tran.generate(fun_name, casadi_codegen_opts)
        if opts['generate_hess']:

            if is_terminal:
                fun_name = con_name + '_constr_h_e_fun_jac_uxt_zt_hess'
            else:
                fun_name = con_name + '_constr_h_fun_jac_uxt_zt_hess'

            # adjoint
            adj_ux = ca.jtimes(con_h_expr, ca.vertcat(u, x), lam_h, True)
            # hessian
            hess_ux = ca.jacobian(adj_ux, ca.vertcat(u, x))

            adj_z = ca.jtimes(con_h_expr, z, lam_h, True)
            hess_z = ca.jacobian(adj_z, z)

            # set up functions
            constraint_fun_jac_tran_hess = \
                ca.Function(fun_name, [x, u, lam_h, z, p], \
                    [con_h_expr, jac_ux_t, hess_ux, jac_z_t, hess_z])

            # generate C code
            constraint_fun_jac_tran_hess.generate(fun_name, casadi_codegen_opts)

        if is_terminal:
            fun_name = con_name + '_constr_h_e_fun'
        else:
            fun_name = con_name + '_constr_h_fun'
        h_fun = ca.Function(fun_name, [x, u, z, p], [con_h_expr])
        h_fun.generate(fun_name, casadi_codegen_opts)

    else: # BGP constraint
        if is_terminal:
            fun_name = con_name + '_phi_e_constraint'
            r = model.con_r_in_phi_e
            con_r_expr = model.con_r_expr_e
        else:
            fun_name = con_name + '_phi_constraint'
            r = model.con_r_in_phi
            con_r_expr = model.con_r_expr

        nphi = casadi_length(con_phi_expr)
        con_phi_expr_x_u_z = ca.substitute(con_phi_expr, r, con_r_expr)
        phi_jac_u = ca.jacobian(con_phi_expr_x_u_z, u)
        phi_jac_x = ca.jacobian(con_phi_expr_x_u_z, x)
        phi_jac_z = ca.jacobian(con_phi_expr_x_u_z, z)

        hess = ca.hessian(con_phi_expr[0], r)[0]
        for i in range(1, nphi):
            hess = ca.vertcat(hess, ca.hessian(con_phi_expr[i], r)[0])

        r_jac_u = ca.jacobian(con_r_expr, u)
        r_jac_x = ca.jacobian(con_r_expr, x)

        constraint_phi = \
            ca.Function(fun_name, [x, u, z, p], \
                [con_phi_expr_x_u_z, \
                ca.vertcat(ca.transpose(phi_jac_u), ca.transpose(phi_jac_x)), \
                ca.transpose(phi_jac_z), \
                hess,
                ca.vertcat(ca.transpose(r_jac_u), ca.transpose(r_jac_x))])

        constraint_phi.generate(fun_name, casadi_codegen_opts)

    # change directory back
    os.chdir(cwd)

    return