def ocp_generate_external_functions(acados_ocp: AcadosOcp, model: AcadosModel):

    model = make_model_consistent(model)

    if acados_ocp.solver_options.hessian_approx == 'EXACT':
        opts = dict(generate_hess=1)
    else:
        opts = dict(generate_hess=0)

    # create code_export_dir, model_dir
    code_export_dir = acados_ocp.code_export_directory
    opts['code_export_directory'] = code_export_dir
    model_dir = os.path.join(code_export_dir, model.name + '_model')
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    check_casadi_version()
    # TODO: remove dir gen from all the generate_c_* functions
    if acados_ocp.model.dyn_ext_fun_type == 'casadi':
        if acados_ocp.solver_options.integrator_type == 'ERK':
            generate_c_code_explicit_ode(model, opts)
        elif acados_ocp.solver_options.integrator_type == 'IRK':
            generate_c_code_implicit_ode(model, opts)
        elif acados_ocp.solver_options.integrator_type == 'LIFTED_IRK':
            generate_c_code_implicit_ode(model, opts)
        elif acados_ocp.solver_options.integrator_type == 'GNSF':
            generate_c_code_gnsf(model, opts)
        elif acados_ocp.solver_options.integrator_type == 'DISCRETE':
            generate_c_code_discrete_dynamics(model, opts)
        else:
            raise Exception("ocp_generate_external_functions: unknown integrator type.")
    else:
        target_location = os.path.join(code_export_dir, model_dir, model.dyn_generic_source)
        shutil.copyfile(model.dyn_generic_source, target_location)

    if acados_ocp.dims.nphi > 0 or acados_ocp.dims.nh > 0:
        generate_c_code_constraint(model, model.name, False, opts)

    if acados_ocp.dims.nphi_e > 0 or acados_ocp.dims.nh_e > 0:
        generate_c_code_constraint(model, model.name, True, opts)

    if acados_ocp.cost.cost_type_0 == 'NONLINEAR_LS':
        generate_c_code_nls_cost(model, model.name, 'initial', opts)
    elif acados_ocp.cost.cost_type_0 == 'CONVEX_OVER_NONLINEAR':
        generate_c_code_conl_cost(model, model.name, 'initial', opts)
    elif acados_ocp.cost.cost_type_0 == 'EXTERNAL':
        generate_c_code_external_cost(model, 'initial', opts)

    if acados_ocp.cost.cost_type == 'NONLINEAR_LS':
        generate_c_code_nls_cost(model, model.name, 'path', opts)
    elif acados_ocp.cost.cost_type == 'CONVEX_OVER_NONLINEAR':
        generate_c_code_conl_cost(model, model.name, 'path', opts)
    elif acados_ocp.cost.cost_type == 'EXTERNAL':
        generate_c_code_external_cost(model, 'path', opts)

    if acados_ocp.cost.cost_type_e == 'NONLINEAR_LS':
        generate_c_code_nls_cost(model, model.name, 'terminal', opts)
    elif acados_ocp.cost.cost_type_e == 'CONVEX_OVER_NONLINEAR':
        generate_c_code_conl_cost(model, model.name, 'terminal', opts)
    elif acados_ocp.cost.cost_type_e == 'EXTERNAL':
        generate_c_code_external_cost(model, 'terminal', opts)