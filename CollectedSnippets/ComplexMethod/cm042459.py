def generate(cls, acados_ocp: AcadosOcp, json_file='acados_ocp_nlp.json', simulink_opts=None, cmake_builder: CMakeBuilder = None):
        """
        Generates the code for an acados OCP solver, given the description in acados_ocp.
            :param acados_ocp: type AcadosOcp - description of the OCP for acados
            :param json_file: name for the json file used to render the templated code - default: `acados_ocp_nlp.json`
            :param simulink_opts: Options to configure Simulink S-function blocks, mainly to activate possible inputs and
                   outputs; default: `None`
            :param cmake_builder: type :py:class:`~acados_template.builders.CMakeBuilder` generate a `CMakeLists.txt` and use
                   the `CMake` pipeline instead of a `Makefile` (`CMake` seems to be the better option in conjunction with
                   `MS Visual Studio`); default: `None`
        """
        model = acados_ocp.model
        acados_ocp.code_export_directory = os.path.abspath(acados_ocp.code_export_directory)

        # make dims consistent
        make_ocp_dims_consistent(acados_ocp)

        # module dependent post processing
        if acados_ocp.solver_options.integrator_type == 'GNSF':
            if 'gnsf_model' in acados_ocp.__dict__:
                set_up_imported_gnsf_model(acados_ocp)
            else:
                detect_gnsf_structure(acados_ocp)

        if acados_ocp.solver_options.qp_solver == 'PARTIAL_CONDENSING_QPDUNES':
            remove_x0_elimination(acados_ocp)

        # set integrator time automatically
        acados_ocp.solver_options.Tsim = acados_ocp.solver_options.time_steps[0]

        # generate external functions
        ocp_generate_external_functions(acados_ocp, model)

        # dump to json
        acados_ocp.json_file = json_file
        ocp_formulation_json_dump(acados_ocp, simulink_opts=simulink_opts, json_file=json_file)

        # render templates
        ocp_render_templates(acados_ocp, json_file, cmake_builder=cmake_builder, simulink_opts=simulink_opts)

        # copy custom update function
        if acados_ocp.solver_options.custom_update_filename != "" and acados_ocp.solver_options.custom_update_copy:
            target_location = os.path.join(acados_ocp.code_export_directory, acados_ocp.solver_options.custom_update_filename)
            shutil.copyfile(acados_ocp.solver_options.custom_update_filename, target_location)
        if acados_ocp.solver_options.custom_update_header_filename != "" and acados_ocp.solver_options.custom_update_copy:
            target_location = os.path.join(acados_ocp.code_export_directory, acados_ocp.solver_options.custom_update_header_filename)
            shutil.copyfile(acados_ocp.solver_options.custom_update_header_filename, target_location)