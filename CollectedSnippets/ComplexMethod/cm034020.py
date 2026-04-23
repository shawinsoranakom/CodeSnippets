def __init__(self, argument_spec, bypass_checks=False, no_log=False,
                 mutually_exclusive=None, required_together=None,
                 required_one_of=None, add_file_common_args=False,
                 supports_check_mode=False, required_if=None, required_by=None):

        """
        Common code for quickly building an ansible module in Python
        (although you can write modules with anything that can return JSON).

        See :ref:`developing_modules_general` for a general introduction
        and :ref:`developing_program_flow_modules` for more detailed explanation.
        """

        self._name = os.path.basename(__file__)  # initialize name until we can parse from options
        self.argument_spec = argument_spec
        self.supports_check_mode = supports_check_mode
        self.check_mode = False
        self.bypass_checks = bypass_checks
        self.no_log = no_log

        self.mutually_exclusive = mutually_exclusive
        self.required_together = required_together
        self.required_one_of = required_one_of
        self.required_if = required_if
        self.required_by = required_by
        self.cleanup_files = []
        self._debug = False
        self._diff = False
        self._socket_path = None
        self._shell = None
        self._syslog_facility = 'LOG_USER'
        self._verbosity = 0
        # May be used to set modifications to the environment for any
        # run_command invocation
        self.run_command_environ_update = {}
        self._clean = {}

        self.aliases = {}
        self._legal_inputs = []
        self._options_context = list()
        self._tmpdir = None

        if add_file_common_args:
            for k, v in FILE_COMMON_ARGUMENTS.items():
                if k not in self.argument_spec:
                    self.argument_spec[k] = v

        # Save parameter values that should never be logged
        self.no_log_values = set()

        # check the locale as set by the current environment, and reset to
        # a known valid (LANG=C) if it's an invalid/unavailable locale
        self._check_locale()

        self._load_params()
        self._set_internal_properties()

        self.validator = ModuleArgumentSpecValidator(self.argument_spec,
                                                     self.mutually_exclusive,
                                                     self.required_together,
                                                     self.required_one_of,
                                                     self.required_if,
                                                     self.required_by,
                                                     )

        self.validation_result = self.validator.validate(self.params)
        self.params.update(self.validation_result.validated_parameters)
        self.no_log_values.update(self.validation_result._no_log_values)
        self.aliases.update(self.validation_result._aliases)

        try:
            error = self.validation_result.errors[0]
            if isinstance(error, UnsupportedError) and self._ignore_unknown_opts:
                error = None
        except IndexError:
            error = None

        # Fail for validation errors, even in check mode
        if error:
            msg = self.validation_result.errors.msg
            if isinstance(error, UnsupportedError):
                msg = "Unsupported parameters for ({name}) {kind}: {msg}".format(name=self._name, kind='module', msg=msg)

            self.fail_json(msg=msg)

        if self.check_mode and not self.supports_check_mode:
            self.exit_json(skipped=True, msg="remote module (%s) does not support check mode" % self._name)

        # This is for backwards compatibility only.
        self._CHECK_ARGUMENT_TYPES_DISPATCHER = DEFAULT_TYPE_VALIDATORS

        if not self.no_log:
            self._log_invocation()

        # selinux state caching
        self._selinux_enabled = None
        self._selinux_mls_enabled = None
        self._selinux_initial_context = None

        # finally, make sure we're in a logical working dir
        self._set_cwd()