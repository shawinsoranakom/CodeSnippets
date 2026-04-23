def _check_c_locale_coercion(self,
                                 fs_encoding, stream_encoding,
                                 coerce_c_locale,
                                 expected_warnings=None,
                                 coercion_expected=True,
                                 **extra_vars):
        """Check the C locale handling for various configurations

        Parameters:
            fs_encoding: expected sys.getfilesystemencoding() result
            stream_encoding: expected encoding for standard streams
            coerce_c_locale: setting to use for PYTHONCOERCECLOCALE
              None: don't set the variable at all
              str: the value set in the child's environment
            expected_warnings: expected warning lines on stderr
            extra_vars: additional environment variables to set in subprocess
        """
        self.maxDiff = None

        if not AVAILABLE_TARGETS:
            # Locale coercion is disabled when there aren't any target locales
            fs_encoding = EXPECTED_C_LOCALE_FS_ENCODING
            stream_encoding = EXPECTED_C_LOCALE_STREAM_ENCODING
            coercion_expected = False
            if expected_warnings:
                expected_warnings = [LEGACY_LOCALE_WARNING]

        base_var_dict = {
            "LANG": "",
            "LC_CTYPE": "",
            "LC_ALL": "",
            "PYTHONCOERCECLOCALE": "",
            "PYTHONIOENCODING": "",
        }
        base_var_dict.update(extra_vars)
        if coerce_c_locale is not None:
            base_var_dict["PYTHONCOERCECLOCALE"] = coerce_c_locale

        # Check behaviour for the default locale
        _fs_encoding = fs_encoding
        _stream_encoding = stream_encoding
        if not DEFAULT_LOCALE_IS_C and 'LC_ALL' not in extra_vars:
            _fs_encoding = _stream_encoding = DEFAULT_ENCODING
        with self.subTest(default_locale=True,
                          PYTHONCOERCECLOCALE=coerce_c_locale):
            if (EXPECT_COERCION_IN_DEFAULT_LOCALE
                    or (not DEFAULT_LOCALE_IS_C and 'LC_ALL' in extra_vars)):
                _expected_warnings = expected_warnings
                _coercion_expected = coercion_expected
            else:
                _expected_warnings = None
                _coercion_expected = False
            # On Android CLI_COERCION_WARNING is not printed when all the
            # locale environment variables are undefined or empty. When
            # this code path is run with environ['LC_ALL'] == 'C', then
            # LEGACY_LOCALE_WARNING is printed.
            if (support.is_android and
                    _expected_warnings == [CLI_COERCION_WARNING]):
                _expected_warnings = None
            self._check_child_encoding_details(base_var_dict,
                                               _fs_encoding,
                                               _stream_encoding,
                                               None,
                                               _expected_warnings,
                                               _coercion_expected)

        # Check behaviour for explicitly configured locales
        for locale_to_set in EXPECTED_C_LOCALE_EQUIVALENTS:
            for env_var in ("LANG", "LC_CTYPE"):
                with self.subTest(env_var=env_var,
                                  nominal_locale=locale_to_set,
                                  PYTHONCOERCECLOCALE=coerce_c_locale,
                                  PYTHONIOENCODING=""):
                    var_dict = base_var_dict.copy()
                    var_dict[env_var] = locale_to_set
                    # Check behaviour on successful coercion
                    self._check_child_encoding_details(var_dict,
                                                       fs_encoding,
                                                       stream_encoding,
                                                       None,
                                                       expected_warnings,
                                                       coercion_expected)