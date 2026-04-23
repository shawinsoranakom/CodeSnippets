def __init__(self, acados_sim, json_file='acados_sim.json', generate=True, build=True, cmake_builder: CMakeBuilder = None, verbose: bool = True):

        self.solver_created = False
        self.acados_sim = acados_sim
        model_name = acados_sim.model.name
        self.model_name = model_name

        code_export_dir = os.path.abspath(acados_sim.code_export_directory)

        # reuse existing json and casadi functions, when creating integrator from ocp
        if generate and not isinstance(acados_sim, AcadosOcp):
            self.generate(acados_sim, json_file=json_file, cmake_builder=cmake_builder)

        if build:
            self.build(code_export_dir, cmake_builder=cmake_builder, verbose=True)

        # prepare library loading
        lib_prefix = 'lib'
        lib_ext = get_lib_ext()
        if os.name == 'nt':
            lib_prefix = ''

        # Load acados library to avoid unloading the library.
        # This is necessary if acados was compiled with OpenMP, since the OpenMP threads can't be destroyed.
        # Unloading a library which uses OpenMP results in a segfault (on any platform?).
        # see [https://stackoverflow.com/questions/34439956/vc-crash-when-freeing-a-dll-built-with-openmp]
        # or [https://python.hotexamples.com/examples/_ctypes/-/dlclose/python-dlclose-function-examples.html]
        libacados_name = f'{lib_prefix}acados{lib_ext}'
        libacados_filepath = os.path.join(acados_sim.acados_lib_path, libacados_name)
        self.__acados_lib = CDLL(libacados_filepath)
        # find out if acados was compiled with OpenMP
        try:
            self.__acados_lib_uses_omp = getattr(self.__acados_lib, 'omp_get_thread_num') is not None
        except AttributeError as e:
            self.__acados_lib_uses_omp = False
        if self.__acados_lib_uses_omp:
            print('acados was compiled with OpenMP.')
        else:
            print('acados was compiled without OpenMP.')
        libacados_sim_solver_name = f'{lib_prefix}acados_sim_solver_{self.model_name}{lib_ext}'
        self.shared_lib_name = os.path.join(code_export_dir, libacados_sim_solver_name)

        # get shared_lib
        self.shared_lib = CDLL(self.shared_lib_name)

        # create capsule
        getattr(self.shared_lib, f"{model_name}_acados_sim_solver_create_capsule").restype = c_void_p
        self.capsule = getattr(self.shared_lib, f"{model_name}_acados_sim_solver_create_capsule")()

        # create solver
        getattr(self.shared_lib, f"{model_name}_acados_sim_create").argtypes = [c_void_p]
        getattr(self.shared_lib, f"{model_name}_acados_sim_create").restype = c_int
        assert getattr(self.shared_lib, f"{model_name}_acados_sim_create")(self.capsule)==0
        self.solver_created = True

        getattr(self.shared_lib, f"{model_name}_acados_get_sim_opts").argtypes = [c_void_p]
        getattr(self.shared_lib, f"{model_name}_acados_get_sim_opts").restype = c_void_p
        self.sim_opts = getattr(self.shared_lib, f"{model_name}_acados_get_sim_opts")(self.capsule)

        getattr(self.shared_lib, f"{model_name}_acados_get_sim_dims").argtypes = [c_void_p]
        getattr(self.shared_lib, f"{model_name}_acados_get_sim_dims").restype = c_void_p
        self.sim_dims = getattr(self.shared_lib, f"{model_name}_acados_get_sim_dims")(self.capsule)

        getattr(self.shared_lib, f"{model_name}_acados_get_sim_config").argtypes = [c_void_p]
        getattr(self.shared_lib, f"{model_name}_acados_get_sim_config").restype = c_void_p
        self.sim_config = getattr(self.shared_lib, f"{model_name}_acados_get_sim_config")(self.capsule)

        getattr(self.shared_lib, f"{model_name}_acados_get_sim_out").argtypes = [c_void_p]
        getattr(self.shared_lib, f"{model_name}_acados_get_sim_out").restype = c_void_p
        self.sim_out = getattr(self.shared_lib, f"{model_name}_acados_get_sim_out")(self.capsule)

        getattr(self.shared_lib, f"{model_name}_acados_get_sim_in").argtypes = [c_void_p]
        getattr(self.shared_lib, f"{model_name}_acados_get_sim_in").restype = c_void_p
        self.sim_in = getattr(self.shared_lib, f"{model_name}_acados_get_sim_in")(self.capsule)

        getattr(self.shared_lib, f"{model_name}_acados_get_sim_solver").argtypes = [c_void_p]
        getattr(self.shared_lib, f"{model_name}_acados_get_sim_solver").restype = c_void_p
        self.sim_solver = getattr(self.shared_lib, f"{model_name}_acados_get_sim_solver")(self.capsule)

        self.gettable_vectors = ['x', 'u', 'z', 'S_adj']
        self.gettable_matrices = ['S_forw', 'Sx', 'Su', 'S_hess', 'S_algebraic']
        self.gettable_scalars = ['CPUtime', 'time_tot', 'ADtime', 'time_ad', 'LAtime', 'time_la']