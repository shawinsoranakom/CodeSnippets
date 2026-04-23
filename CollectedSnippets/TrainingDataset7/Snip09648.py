def _create_test_db(self, verbosity=1, autoclobber=False, keepdb=False):
        parameters = self._get_test_db_params()
        with self._maindb_connection.cursor() as cursor:
            if self._test_database_create():
                try:
                    self._execute_test_db_creation(
                        cursor, parameters, verbosity, keepdb
                    )
                except Exception as e:
                    if "ORA-01543" not in str(e):
                        # All errors except "tablespace already exists" cancel
                        # tests
                        self.log("Got an error creating the test database: %s" % e)
                        sys.exit(2)
                    if not autoclobber:
                        confirm = input(
                            "It appears the test database, %s, already exists. "
                            "Type 'yes' to delete it, or 'no' to cancel: "
                            % parameters["user"]
                        )
                    if autoclobber or confirm == "yes":
                        if verbosity >= 1:
                            self.log(
                                "Destroying old test database for alias '%s'..."
                                % self.connection.alias
                            )
                        try:
                            self._execute_test_db_destruction(
                                cursor, parameters, verbosity
                            )
                        except DatabaseError as e:
                            if "ORA-29857" in str(e):
                                self._handle_objects_preventing_db_destruction(
                                    cursor, parameters, verbosity, autoclobber
                                )
                            else:
                                # Ran into a database error that isn't about
                                # leftover objects in the tablespace.
                                self.log(
                                    "Got an error destroying the old test database: %s"
                                    % e
                                )
                                sys.exit(2)
                        except Exception as e:
                            self.log(
                                "Got an error destroying the old test database: %s" % e
                            )
                            sys.exit(2)
                        try:
                            self._execute_test_db_creation(
                                cursor, parameters, verbosity, keepdb
                            )
                        except Exception as e:
                            self.log(
                                "Got an error recreating the test database: %s" % e
                            )
                            sys.exit(2)
                    else:
                        self.log("Tests cancelled.")
                        sys.exit(1)

            if self._test_user_create():
                if verbosity >= 1:
                    self.log("Creating test user...")
                try:
                    self._create_test_user(cursor, parameters, verbosity, keepdb)
                except Exception as e:
                    if "ORA-01920" not in str(e):
                        # All errors except "user already exists" cancel tests
                        self.log("Got an error creating the test user: %s" % e)
                        sys.exit(2)
                    if not autoclobber:
                        confirm = input(
                            "It appears the test user, %s, already exists. Type "
                            "'yes' to delete it, or 'no' to cancel: "
                            % parameters["user"]
                        )
                    if autoclobber or confirm == "yes":
                        try:
                            if verbosity >= 1:
                                self.log("Destroying old test user...")
                            self._destroy_test_user(cursor, parameters, verbosity)
                            if verbosity >= 1:
                                self.log("Creating test user...")
                            self._create_test_user(
                                cursor, parameters, verbosity, keepdb
                            )
                        except Exception as e:
                            self.log("Got an error recreating the test user: %s" % e)
                            sys.exit(2)
                    else:
                        self.log("Tests cancelled.")
                        sys.exit(1)
        # Done with main user -- test user and tablespaces created.
        self._maindb_connection.close()
        self._switch_to_test_user(parameters)
        return self.connection.settings_dict["NAME"]