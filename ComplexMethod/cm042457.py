def make_ocp_dims_consistent(acados_ocp: AcadosOcp):
    dims = acados_ocp.dims
    cost = acados_ocp.cost
    constraints = acados_ocp.constraints
    model = acados_ocp.model
    opts = acados_ocp.solver_options

    # nx
    if is_column(model.x):
        dims.nx = casadi_length(model.x)
    else:
        raise Exception('model.x should be column vector!')

    # nu
    if is_empty(model.u):
        dims.nu = 0
    else:
        dims.nu = casadi_length(model.u)

    # nz
    if is_empty(model.z):
        dims.nz = 0
    else:
        dims.nz = casadi_length(model.z)

    # np
    if is_empty(model.p):
        dims.np = 0
    else:
        dims.np = casadi_length(model.p)
    if acados_ocp.parameter_values.shape[0] != dims.np:
        raise Exception('inconsistent dimension np, regarding model.p and parameter_values.' + \
            f'\nGot np = {dims.np}, acados_ocp.parameter_values.shape = {acados_ocp.parameter_values.shape[0]}\n')

    ## cost
    # initial stage - if not set, copy fields from path constraints
    if cost.cost_type_0 is None:
        cost.cost_type_0 = cost.cost_type
        cost.W_0 = cost.W
        cost.Vx_0 = cost.Vx
        cost.Vu_0 = cost.Vu
        cost.Vz_0 = cost.Vz
        cost.yref_0 = cost.yref
        cost.cost_ext_fun_type_0 = cost.cost_ext_fun_type
        model.cost_y_expr_0 = model.cost_y_expr
        model.cost_expr_ext_cost_0 = model.cost_expr_ext_cost
        model.cost_expr_ext_cost_custom_hess_0 = model.cost_expr_ext_cost_custom_hess

        model.cost_psi_expr_0 = model.cost_psi_expr
        model.cost_r_in_psi_expr_0 = model.cost_r_in_psi_expr

    if cost.cost_type_0 == 'LINEAR_LS':
        ny_0 = cost.W_0.shape[0]
        if cost.Vx_0.shape[0] != ny_0 or cost.Vu_0.shape[0] != ny_0:
            raise Exception('inconsistent dimension ny_0, regarding W_0, Vx_0, Vu_0.' + \
                            f'\nGot W_0[{cost.W_0.shape}], Vx_0[{cost.Vx_0.shape}], Vu_0[{cost.Vu_0.shape}]\n')
        if dims.nz != 0 and cost.Vz_0.shape[0] != ny_0:
            raise Exception('inconsistent dimension ny_0, regarding W_0, Vx_0, Vu_0, Vz_0.' + \
                            f'\nGot W_0[{cost.W_0.shape}], Vx_0[{cost.Vx_0.shape}], Vu_0[{cost.Vu_0.shape}], Vz_0[{cost.Vz_0.shape}]\n')
        if cost.Vx_0.shape[1] != dims.nx and ny_0 != 0:
            raise Exception('inconsistent dimension: Vx_0 should have nx columns.')
        if cost.Vu_0.shape[1] != dims.nu and ny_0 != 0:
            raise Exception('inconsistent dimension: Vu_0 should have nu columns.')
        if cost.yref_0.shape[0] != ny_0:
            raise Exception('inconsistent dimension: regarding W_0, yref_0.' + \
                            f'\nGot W_0[{cost.W_0.shape}], yref_0[{cost.yref_0.shape}]\n')
        dims.ny_0 = ny_0

    elif cost.cost_type_0 == 'NONLINEAR_LS':
        ny_0 = cost.W_0.shape[0]
        if is_empty(model.cost_y_expr_0) and ny_0 != 0:
            raise Exception('inconsistent dimension ny_0: regarding W_0, cost_y_expr.')
        elif casadi_length(model.cost_y_expr_0) != ny_0:
            raise Exception('inconsistent dimension ny_0: regarding W_0, cost_y_expr.')
        if cost.yref_0.shape[0] != ny_0:
            raise Exception('inconsistent dimension: regarding W_0, yref_0.' + \
                            f'\nGot W_0[{cost.W.shape}], yref_0[{cost.yref_0.shape}]\n')
        dims.ny_0 = ny_0

    elif cost.cost_type_0 == 'CONVEX_OVER_NONLINEAR':
        if is_empty(model.cost_y_expr_0):
            raise Exception('cost_y_expr_0 and/or cost_y_expr not provided.')
        ny_0 = casadi_length(model.cost_y_expr_0)
        if is_empty(model.cost_r_in_psi_expr_0) or casadi_length(model.cost_r_in_psi_expr_0) != ny_0:
            raise Exception('inconsistent dimension ny_0: regarding cost_y_expr_0 and cost_r_in_psi_0.')
        if is_empty(model.cost_psi_expr_0) or casadi_length(model.cost_psi_expr_0) != 1:
            raise Exception('cost_psi_expr_0 not provided or not scalar-valued.')
        if cost.yref_0.shape[0] != ny_0:
            raise Exception('inconsistent dimension: regarding yref_0 and cost_y_expr_0, cost_r_in_psi_0.')
        dims.ny_0 = ny_0

        if not (opts.hessian_approx=='EXACT' and opts.exact_hess_cost==False) and opts.hessian_approx != 'GAUSS_NEWTON':
            raise Exception("\nWith CONVEX_OVER_NONLINEAR cost type, possible Hessian approximations are:\n"
            "GAUSS_NEWTON or EXACT with 'exact_hess_cost' == False.\n")

    elif cost.cost_type_0 == 'EXTERNAL':
        if opts.hessian_approx == 'GAUSS_NEWTON' and opts.ext_cost_num_hess == 0 and model.cost_expr_ext_cost_custom_hess_0 is None:
            print("\nWARNING: Gauss-Newton Hessian approximation with EXTERNAL cost type not possible!\n"
            "got cost_type_0: EXTERNAL, hessian_approx: 'GAUSS_NEWTON.'\n"
            "GAUSS_NEWTON hessian is only supported for cost_types [NON]LINEAR_LS.\n"
            "If you continue, acados will proceed computing the exact hessian for the cost term.\n"
            "Note: There is also the option to use the external cost module with a numerical hessian approximation (see `ext_cost_num_hess`).\n"
            "OR the option to provide a symbolic custom hessian approximation (see `cost_expr_ext_cost_custom_hess`).\n")

    # path
    if cost.cost_type == 'LINEAR_LS':
        ny = cost.W.shape[0]
        if cost.Vx.shape[0] != ny or cost.Vu.shape[0] != ny:
            raise Exception('inconsistent dimension ny, regarding W, Vx, Vu.' + \
                            f'\nGot W[{cost.W.shape}], Vx[{cost.Vx.shape}], Vu[{cost.Vu.shape}]\n')
        if dims.nz != 0 and cost.Vz.shape[0] != ny:
            raise Exception('inconsistent dimension ny, regarding W, Vx, Vu, Vz.' + \
                            f'\nGot W[{cost.W.shape}], Vx[{cost.Vx.shape}], Vu[{cost.Vu.shape}], Vz[{cost.Vz.shape}]\n')
        if cost.Vx.shape[1] != dims.nx and ny != 0:
            raise Exception('inconsistent dimension: Vx should have nx columns.')
        if cost.Vu.shape[1] != dims.nu and ny != 0:
            raise Exception('inconsistent dimension: Vu should have nu columns.')
        if cost.yref.shape[0] != ny:
            raise Exception('inconsistent dimension: regarding W, yref.' + \
                            f'\nGot W[{cost.W.shape}], yref[{cost.yref.shape}]\n')
        dims.ny = ny

    elif cost.cost_type == 'NONLINEAR_LS':
        ny = cost.W.shape[0]
        if is_empty(model.cost_y_expr) and ny != 0:
            raise Exception('inconsistent dimension ny: regarding W, cost_y_expr.')
        elif casadi_length(model.cost_y_expr) != ny:
            raise Exception('inconsistent dimension ny: regarding W, cost_y_expr.')
        if cost.yref.shape[0] != ny:
            raise Exception('inconsistent dimension: regarding W, yref.' + \
                            f'\nGot W[{cost.W.shape}], yref[{cost.yref.shape}]\n')
        dims.ny = ny

    elif cost.cost_type == 'CONVEX_OVER_NONLINEAR':
        if is_empty(model.cost_y_expr):
            raise Exception('cost_y_expr and/or cost_y_expr not provided.')
        ny = casadi_length(model.cost_y_expr)
        if is_empty(model.cost_r_in_psi_expr) or casadi_length(model.cost_r_in_psi_expr) != ny:
            raise Exception('inconsistent dimension ny: regarding cost_y_expr and cost_r_in_psi.')
        if is_empty(model.cost_psi_expr) or casadi_length(model.cost_psi_expr) != 1:
            raise Exception('cost_psi_expr not provided or not scalar-valued.')
        if cost.yref.shape[0] != ny:
            raise Exception('inconsistent dimension: regarding yref and cost_y_expr, cost_r_in_psi.')
        dims.ny = ny

        if not (opts.hessian_approx=='EXACT' and opts.exact_hess_cost==False) and opts.hessian_approx != 'GAUSS_NEWTON':
            raise Exception("\nWith CONVEX_OVER_NONLINEAR cost type, possible Hessian approximations are:\n"
            "GAUSS_NEWTON or EXACT with 'exact_hess_cost' == False.\n")


    elif cost.cost_type == 'EXTERNAL':
        if opts.hessian_approx == 'GAUSS_NEWTON' and opts.ext_cost_num_hess == 0 and model.cost_expr_ext_cost_custom_hess is None:
            print("\nWARNING: Gauss-Newton Hessian approximation with EXTERNAL cost type not possible!\n"
            "got cost_type: EXTERNAL, hessian_approx: 'GAUSS_NEWTON.'\n"
            "GAUSS_NEWTON hessian is only supported for cost_types [NON]LINEAR_LS.\n"
            "If you continue, acados will proceed computing the exact hessian for the cost term.\n"
            "Note: There is also the option to use the external cost module with a numerical hessian approximation (see `ext_cost_num_hess`).\n"
            "OR the option to provide a symbolic custom hessian approximation (see `cost_expr_ext_cost_custom_hess`).\n")

    # terminal
    if cost.cost_type_e == 'LINEAR_LS':
        ny_e = cost.W_e.shape[0]
        if cost.Vx_e.shape[0] != ny_e:
            raise Exception('inconsistent dimension ny_e: regarding W_e, cost_y_expr_e.' + \
                f'\nGot W_e[{cost.W_e.shape}], Vx_e[{cost.Vx_e.shape}]')
        if cost.Vx_e.shape[1] != dims.nx and ny_e != 0:
            raise Exception('inconsistent dimension: Vx_e should have nx columns.')
        if cost.yref_e.shape[0] != ny_e:
            raise Exception('inconsistent dimension: regarding W_e, yref_e.')
        dims.ny_e = ny_e

    elif cost.cost_type_e == 'NONLINEAR_LS':
        ny_e = cost.W_e.shape[0]
        if is_empty(model.cost_y_expr_e) and ny_e != 0:
            raise Exception('inconsistent dimension ny_e: regarding W_e, cost_y_expr_e.')
        elif casadi_length(model.cost_y_expr_e) != ny_e:
            raise Exception('inconsistent dimension ny_e: regarding W_e, cost_y_expr_e.')
        if cost.yref_e.shape[0] != ny_e:
            raise Exception('inconsistent dimension: regarding W_e, yref_e.')
        dims.ny_e = ny_e

    elif cost.cost_type_e == 'CONVEX_OVER_NONLINEAR':
        if is_empty(model.cost_y_expr_e):
            raise Exception('cost_y_expr_e not provided.')
        ny_e = casadi_length(model.cost_y_expr_e)
        if is_empty(model.cost_r_in_psi_expr_e) or casadi_length(model.cost_r_in_psi_expr_e) != ny_e:
            raise Exception('inconsistent dimension ny_e: regarding cost_y_expr_e and cost_r_in_psi_e.')
        if is_empty(model.cost_psi_expr_e) or casadi_length(model.cost_psi_expr_e) != 1:
            raise Exception('cost_psi_expr_e not provided or not scalar-valued.')
        if cost.yref_e.shape[0] != ny_e:
            raise Exception('inconsistent dimension: regarding yref_e and cost_y_expr_e, cost_r_in_psi_e.')
        dims.ny_e = ny_e

        if not (opts.hessian_approx=='EXACT' and opts.exact_hess_cost==False) and opts.hessian_approx != 'GAUSS_NEWTON':
            raise Exception("\nWith CONVEX_OVER_NONLINEAR cost type, possible Hessian approximations are:\n"
            "GAUSS_NEWTON or EXACT with 'exact_hess_cost' == False.\n")



    elif cost.cost_type_e == 'EXTERNAL':
        if opts.hessian_approx == 'GAUSS_NEWTON' and opts.ext_cost_num_hess == 0 and model.cost_expr_ext_cost_custom_hess_e is None:
            print("\nWARNING: Gauss-Newton Hessian approximation with EXTERNAL cost type not possible!\n"
            "got cost_type_e: EXTERNAL, hessian_approx: 'GAUSS_NEWTON.'\n"
            "GAUSS_NEWTON hessian is only supported for cost_types [NON]LINEAR_LS.\n"
            "If you continue, acados will proceed computing the exact hessian for the cost term.\n"
            "Note: There is also the option to use the external cost module with a numerical hessian approximation (see `ext_cost_num_hess`).\n"
            "OR the option to provide a symbolic custom hessian approximation (see `cost_expr_ext_cost_custom_hess`).\n")

    ## constraints
    # initial
    this_shape = constraints.lbx_0.shape
    other_shape = constraints.ubx_0.shape
    if not this_shape == other_shape:
        raise Exception('lbx_0, ubx_0 have different shapes!')
    if not is_column(constraints.lbx_0):
        raise Exception('lbx_0, ubx_0 must be column vectors!')
    dims.nbx_0 = constraints.lbx_0.size

    if all(constraints.lbx_0 == constraints.ubx_0) and dims.nbx_0 == dims.nx \
        and dims.nbxe_0 is None \
        and (constraints.idxbxe_0.shape == constraints.idxbx_0.shape)\
            and all(constraints.idxbxe_0 == constraints.idxbx_0):
        # case: x0 was set: nbx0 are all equlities.
        dims.nbxe_0 = dims.nbx_0
    elif constraints.idxbxe_0 is not None:
        dims.nbxe_0 = constraints.idxbxe_0.shape[0]
    elif dims.nbxe_0 is None:
        # case: x0 and idxbxe_0 were not set -> dont assume nbx0 to be equality constraints.
        dims.nbxe_0 = 0

    # path
    nbx = constraints.idxbx.shape[0]
    if constraints.ubx.shape[0] != nbx or constraints.lbx.shape[0] != nbx:
        raise Exception('inconsistent dimension nbx, regarding idxbx, ubx, lbx.')
    else:
        dims.nbx = nbx

    nbu = constraints.idxbu.shape[0]
    if constraints.ubu.shape[0] != nbu or constraints.lbu.shape[0] != nbu:
        raise Exception('inconsistent dimension nbu, regarding idxbu, ubu, lbu.')
    else:
        dims.nbu = nbu

    ng = constraints.lg.shape[0]
    if constraints.ug.shape[0] != ng or constraints.C.shape[0] != ng \
       or constraints.D.shape[0] != ng:
        raise Exception('inconsistent dimension ng, regarding lg, ug, C, D.')
    else:
        dims.ng = ng

    if not is_empty(model.con_h_expr):
        nh = casadi_length(model.con_h_expr)
    else:
        nh = 0

    if constraints.uh.shape[0] != nh or constraints.lh.shape[0] != nh:
        raise Exception('inconsistent dimension nh, regarding lh, uh, con_h_expr.')
    else:
        dims.nh = nh

    if is_empty(model.con_phi_expr):
        dims.nphi = 0
        dims.nr = 0
    else:
        dims.nphi = casadi_length(model.con_phi_expr)
        if is_empty(model.con_r_expr):
            raise Exception('convex over nonlinear constraints: con_r_expr but con_phi_expr is nonempty')
        else:
            dims.nr = casadi_length(model.con_r_expr)

    # terminal
    nbx_e = constraints.idxbx_e.shape[0]
    if constraints.ubx_e.shape[0] != nbx_e or constraints.lbx_e.shape[0] != nbx_e:
        raise Exception('inconsistent dimension nbx_e, regarding idxbx_e, ubx_e, lbx_e.')
    else:
        dims.nbx_e = nbx_e

    ng_e = constraints.lg_e.shape[0]
    if constraints.ug_e.shape[0] != ng_e or constraints.C_e.shape[0] != ng_e:
        raise Exception('inconsistent dimension ng_e, regarding_e lg_e, ug_e, C_e.')
    else:
        dims.ng_e = ng_e

    if not is_empty(model.con_h_expr_e):
        nh_e = casadi_length(model.con_h_expr_e)
    else:
        nh_e = 0

    if constraints.uh_e.shape[0] != nh_e or constraints.lh_e.shape[0] != nh_e:
        raise Exception('inconsistent dimension nh_e, regarding lh_e, uh_e, con_h_expr_e.')
    else:
        dims.nh_e = nh_e

    if is_empty(model.con_phi_expr_e):
        dims.nphi_e = 0
        dims.nr_e = 0
    else:
        dims.nphi_e = casadi_length(model.con_phi_expr_e)
        if is_empty(model.con_r_expr_e):
            raise Exception('convex over nonlinear constraints: con_r_expr_e but con_phi_expr_e is nonempty')
        else:
            dims.nr_e = casadi_length(model.con_r_expr_e)

    # Slack dimensions
    nsbx = constraints.idxsbx.shape[0]
    if nsbx > nbx:
        raise Exception(f'inconsistent dimension nsbx = {nsbx}. Is greater than nbx = {nbx}.')
    if is_empty(constraints.lsbx):
        constraints.lsbx = np.zeros((nsbx,))
    elif constraints.lsbx.shape[0] != nsbx:
        raise Exception('inconsistent dimension nsbx, regarding idxsbx, lsbx.')
    if is_empty(constraints.usbx):
        constraints.usbx = np.zeros((nsbx,))
    elif constraints.usbx.shape[0] != nsbx:
        raise Exception('inconsistent dimension nsbx, regarding idxsbx, usbx.')
    dims.nsbx = nsbx

    nsbu = constraints.idxsbu.shape[0]
    if nsbu > nbu:
        raise Exception(f'inconsistent dimension nsbu = {nsbu}. Is greater than nbu = {nbu}.')
    if is_empty(constraints.lsbu):
        constraints.lsbu = np.zeros((nsbu,))
    elif constraints.lsbu.shape[0] != nsbu:
        raise Exception('inconsistent dimension nsbu, regarding idxsbu, lsbu.')
    if is_empty(constraints.usbu):
        constraints.usbu = np.zeros((nsbu,))
    elif constraints.usbu.shape[0] != nsbu:
        raise Exception('inconsistent dimension nsbu, regarding idxsbu, usbu.')
    dims.nsbu = nsbu

    nsh = constraints.idxsh.shape[0]
    if nsh > nh:
        raise Exception(f'inconsistent dimension nsh = {nsh}. Is greater than nh = {nh}.')
    if is_empty(constraints.lsh):
        constraints.lsh = np.zeros((nsh,))
    elif constraints.lsh.shape[0] != nsh:
        raise Exception('inconsistent dimension nsh, regarding idxsh, lsh.')
    if is_empty(constraints.ush):
        constraints.ush = np.zeros((nsh,))
    elif constraints.ush.shape[0] != nsh:
        raise Exception('inconsistent dimension nsh, regarding idxsh, ush.')
    dims.nsh = nsh

    nsphi = constraints.idxsphi.shape[0]
    if nsphi > dims.nphi:
        raise Exception(f'inconsistent dimension nsphi = {nsphi}. Is greater than nphi = {dims.nphi}.')
    if is_empty(constraints.lsphi):
        constraints.lsphi = np.zeros((nsphi,))
    elif constraints.lsphi.shape[0] != nsphi:
        raise Exception('inconsistent dimension nsphi, regarding idxsphi, lsphi.')
    if is_empty(constraints.usphi):
        constraints.usphi = np.zeros((nsphi,))
    elif constraints.usphi.shape[0] != nsphi:
        raise Exception('inconsistent dimension nsphi, regarding idxsphi, usphi.')
    dims.nsphi = nsphi

    nsg = constraints.idxsg.shape[0]
    if nsg > ng:
        raise Exception(f'inconsistent dimension nsg = {nsg}. Is greater than ng = {ng}.')
    if is_empty(constraints.lsg):
        constraints.lsg = np.zeros((nsg,))
    elif constraints.lsg.shape[0] != nsg:
        raise Exception('inconsistent dimension nsg, regarding idxsg, lsg.')
    if is_empty(constraints.usg):
        constraints.usg = np.zeros((nsg,))
    elif constraints.usg.shape[0] != nsg:
        raise Exception('inconsistent dimension nsg, regarding idxsg, usg.')
    dims.nsg = nsg

    ns = nsbx + nsbu + nsh + nsg + nsphi
    wrong_field = ""
    if cost.Zl.shape[0] != ns:
        wrong_field = "Zl"
        dim = cost.Zl.shape[0]
    elif cost.Zu.shape[0] != ns:
        wrong_field = "Zu"
        dim = cost.Zu.shape[0]
    elif cost.zl.shape[0] != ns:
        wrong_field = "zl"
        dim = cost.zl.shape[0]
    elif cost.zu.shape[0] != ns:
        wrong_field = "zu"
        dim = cost.zu.shape[0]

    if wrong_field != "":
        raise Exception(f'Inconsistent size for field {wrong_field}, with dimension {dim}, \n\t'\
            + f'Detected ns = {ns} = nsbx + nsbu + nsg + nsh + nsphi.\n\t'\
            + f'With nsbx = {nsbx}, nsbu = {nsbu}, nsg = {nsg}, nsh = {nsh}, nsphi = {nsphi}')

    dims.ns = ns

    nsbx_e = constraints.idxsbx_e.shape[0]
    if nsbx_e > nbx_e:
        raise Exception(f'inconsistent dimension nsbx_e = {nsbx_e}. Is greater than nbx_e = {nbx_e}.')
    if is_empty(constraints.lsbx_e):
        constraints.lsbx_e = np.zeros((nsbx_e,))
    elif constraints.lsbx_e.shape[0] != nsbx_e:
        raise Exception('inconsistent dimension nsbx_e, regarding idxsbx_e, lsbx_e.')
    if is_empty(constraints.usbx_e):
        constraints.usbx_e = np.zeros((nsbx_e,))
    elif constraints.usbx_e.shape[0] != nsbx_e:
        raise Exception('inconsistent dimension nsbx_e, regarding idxsbx_e, usbx_e.')
    dims.nsbx_e = nsbx_e

    nsh_e = constraints.idxsh_e.shape[0]
    if nsh_e > nh_e:
        raise Exception(f'inconsistent dimension nsh_e = {nsh_e}. Is greater than nh_e = {nh_e}.')
    if is_empty(constraints.lsh_e):
        constraints.lsh_e = np.zeros((nsh_e,))
    elif constraints.lsh_e.shape[0] != nsh_e:
        raise Exception('inconsistent dimension nsh_e, regarding idxsh_e, lsh_e.')
    if is_empty(constraints.ush_e):
        constraints.ush_e = np.zeros((nsh_e,))
    elif constraints.ush_e.shape[0] != nsh_e:
        raise Exception('inconsistent dimension nsh_e, regarding idxsh_e, ush_e.')
    dims.nsh_e = nsh_e

    nsg_e = constraints.idxsg_e.shape[0]
    if nsg_e > ng_e:
        raise Exception(f'inconsistent dimension nsg_e = {nsg_e}. Is greater than ng_e = {ng_e}.')
    if is_empty(constraints.lsg_e):
        constraints.lsg_e = np.zeros((nsg_e,))
    elif constraints.lsg_e.shape[0] != nsg_e:
        raise Exception('inconsistent dimension nsg_e, regarding idxsg_e, lsg_e.')
    if is_empty(constraints.usg_e):
        constraints.usg_e = np.zeros((nsg_e,))
    elif constraints.usg_e.shape[0] != nsg_e:
        raise Exception('inconsistent dimension nsg_e, regarding idxsg_e, usg_e.')
    dims.nsg_e = nsg_e

    nsphi_e = constraints.idxsphi_e.shape[0]
    if nsphi_e > dims.nphi_e:
        raise Exception(f'inconsistent dimension nsphi_e = {nsphi_e}. Is greater than nphi_e = {dims.nphi_e}.')
    if is_empty(constraints.lsphi_e):
        constraints.lsphi_e = np.zeros((nsphi_e,))
    elif constraints.lsphi_e.shape[0] != nsphi_e:
        raise Exception('inconsistent dimension nsphi_e, regarding idxsphi_e, lsphi_e.')
    if is_empty(constraints.usphi_e):
        constraints.usphi_e = np.zeros((nsphi_e,))
    elif constraints.usphi_e.shape[0] != nsphi_e:
        raise Exception('inconsistent dimension nsphi_e, regarding idxsphi_e, usphi_e.')
    dims.nsphi_e = nsphi_e

    # terminal
    ns_e = nsbx_e + nsh_e + nsg_e + nsphi_e
    wrong_field = ""
    if cost.Zl_e.shape[0] != ns_e:
        wrong_field = "Zl_e"
        dim = cost.Zl_e.shape[0]
    elif cost.Zu_e.shape[0] != ns_e:
        wrong_field = "Zu_e"
        dim = cost.Zu_e.shape[0]
    elif cost.zl_e.shape[0] != ns_e:
        wrong_field = "zl_e"
        dim = cost.zl_e.shape[0]
    elif cost.zu_e.shape[0] != ns_e:
        wrong_field = "zu_e"
        dim = cost.zu_e.shape[0]

    if wrong_field != "":
        raise Exception(f'Inconsistent size for field {wrong_field}, with dimension {dim}, \n\t'\
            + f'Detected ns_e = {ns_e} = nsbx_e + nsg_e + nsh_e + nsphi_e.\n\t'\
            + f'With nsbx_e = {nsbx_e}, nsg_e = {nsg_e}, nsh_e = {nsh_e}, nsphi_e = {nsphi_e}')

    dims.ns_e = ns_e

    # discretization
    if is_empty(opts.time_steps) and is_empty(opts.shooting_nodes):
        # uniform discretization
        opts.time_steps = opts.tf / dims.N * np.ones((dims.N,))

    elif not is_empty(opts.shooting_nodes):
        if np.shape(opts.shooting_nodes)[0] != dims.N+1:
            raise Exception('inconsistent dimension N, regarding shooting_nodes.')

        time_steps = opts.shooting_nodes[1:] - opts.shooting_nodes[0:-1]
        # identify constant time_steps: due to numerical reasons the content of time_steps might vary a bit
        avg_time_steps = np.average(time_steps)
        # criterion for constant time step detection: the min/max difference in values normalized by the average
        check_const_time_step = (np.max(time_steps)-np.min(time_steps)) / avg_time_steps
        # if the criterion is small, we have a constant time_step
        if check_const_time_step < 1e-9:
            time_steps[:] = avg_time_steps  # if we have a constant time_step: apply the average time_step

        opts.time_steps = time_steps

    elif (not is_empty(opts.time_steps)) and (not is_empty(opts.shooting_nodes)):
        Exception('Please provide either time_steps or shooting_nodes for nonuniform discretization')

    tf = np.sum(opts.time_steps)
    if (tf - opts.tf) / tf > 1e-15:
        raise Exception(f'Inconsistent discretization: {opts.tf}'\
            f' = tf != sum(opts.time_steps) = {tf}.')

    # num_steps
    if isinstance(opts.sim_method_num_steps, np.ndarray) and opts.sim_method_num_steps.size == 1:
        opts.sim_method_num_steps = opts.sim_method_num_steps.item()

    if isinstance(opts.sim_method_num_steps, (int, float)) and opts.sim_method_num_steps % 1 == 0:
        opts.sim_method_num_steps = opts.sim_method_num_steps * np.ones((dims.N,), dtype=np.int64)
    elif isinstance(opts.sim_method_num_steps, np.ndarray) and opts.sim_method_num_steps.size == dims.N \
           and np.all(np.equal(np.mod(opts.sim_method_num_steps, 1), 0)):
        opts.sim_method_num_steps = np.reshape(opts.sim_method_num_steps, (dims.N,)).astype(np.int64)
    else:
        raise Exception("Wrong value for sim_method_num_steps. Should be either int or array of ints of shape (N,).")

    # num_stages
    if isinstance(opts.sim_method_num_stages, np.ndarray) and opts.sim_method_num_stages.size == 1:
        opts.sim_method_num_stages = opts.sim_method_num_stages.item()

    if isinstance(opts.sim_method_num_stages, (int, float)) and opts.sim_method_num_stages % 1 == 0:
        opts.sim_method_num_stages = opts.sim_method_num_stages * np.ones((dims.N,), dtype=np.int64)
    elif isinstance(opts.sim_method_num_stages, np.ndarray) and opts.sim_method_num_stages.size == dims.N \
           and np.all(np.equal(np.mod(opts.sim_method_num_stages, 1), 0)):
        opts.sim_method_num_stages = np.reshape(opts.sim_method_num_stages, (dims.N,)).astype(np.int64)
    else:
        raise Exception("Wrong value for sim_method_num_stages. Should be either int or array of ints of shape (N,).")

    # jac_reuse
    if isinstance(opts.sim_method_jac_reuse, np.ndarray) and opts.sim_method_jac_reuse.size == 1:
        opts.sim_method_jac_reuse = opts.sim_method_jac_reuse.item()

    if isinstance(opts.sim_method_jac_reuse, (int, float)) and opts.sim_method_jac_reuse % 1 == 0:
        opts.sim_method_jac_reuse = opts.sim_method_jac_reuse * np.ones((dims.N,), dtype=np.int64)
    elif isinstance(opts.sim_method_jac_reuse, np.ndarray) and opts.sim_method_jac_reuse.size == dims.N \
           and np.all(np.equal(np.mod(opts.sim_method_jac_reuse, 1), 0)):
        opts.sim_method_jac_reuse = np.reshape(opts.sim_method_jac_reuse, (dims.N,)).astype(np.int64)
    else:
        raise Exception("Wrong value for sim_method_jac_reuse. Should be either int or array of ints of shape (N,).")