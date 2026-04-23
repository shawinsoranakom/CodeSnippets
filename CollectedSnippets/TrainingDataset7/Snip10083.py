def _build_migration_list(self, graph=None):
        """
        Chop the lists of operations up into migrations with dependencies on
        each other. Do this by going through an app's list of operations until
        one is found that has an outgoing dependency that isn't in another
        app's migration yet (hasn't been chopped off its list). Then chop off
        the operations before it into a migration and move onto the next app.
        If the loops completes without doing anything, there's a circular
        dependency (which _should_ be impossible as the operations are
        all split at this point so they can't depend and be depended on).
        """
        self.migrations = {}
        num_ops = sum(len(x) for x in self.generated_operations.values())
        chop_mode = False
        while num_ops:
            # On every iteration, we step through all the apps and see if there
            # is a completed set of operations.
            # If we find that a subset of the operations are complete we can
            # try to chop it off from the rest and continue, but we only
            # do this if we've already been through the list once before
            # without any chopping and nothing has changed.
            for app_label in sorted(self.generated_operations):
                chopped = []
                dependencies = set()
                for operation in list(self.generated_operations[app_label]):
                    deps_satisfied = True
                    operation_dependencies = set()
                    for dep in operation._auto_deps:
                        # Temporarily resolve the swappable dependency to
                        # prevent circular references. While keeping the
                        # dependency checks on the resolved model, add the
                        # swappable dependencies.
                        original_dep = dep
                        dep, is_swappable_dep = self._resolve_dependency(dep)
                        if dep.app_label != app_label:
                            # External app dependency. See if it's not yet
                            # satisfied.
                            for other_operation in self.generated_operations.get(
                                dep.app_label, []
                            ):
                                if self.check_dependency(other_operation, dep):
                                    deps_satisfied = False
                                    break
                            if not deps_satisfied:
                                break
                            else:
                                if is_swappable_dep:
                                    operation_dependencies.add(
                                        (
                                            original_dep.app_label,
                                            original_dep.model_name,
                                        )
                                    )
                                elif dep.app_label in self.migrations:
                                    operation_dependencies.add(
                                        (
                                            dep.app_label,
                                            self.migrations[dep.app_label][-1].name,
                                        )
                                    )
                                else:
                                    # If we can't find the other app, we add a
                                    # first/last dependency, but only if we've
                                    # already been through once and checked
                                    # everything.
                                    if chop_mode:
                                        # If the app already exists, we add a
                                        # dependency on the last migration, as
                                        # we don't know which migration
                                        # contains the target field. If it's
                                        # not yet migrated or has no
                                        # migrations, we use __first__.
                                        if graph and graph.leaf_nodes(dep.app_label):
                                            operation_dependencies.add(
                                                graph.leaf_nodes(dep.app_label)[0]
                                            )
                                        else:
                                            operation_dependencies.add(
                                                (dep.app_label, "__first__")
                                            )
                                    else:
                                        deps_satisfied = False
                    if deps_satisfied:
                        chopped.append(operation)
                        dependencies.update(operation_dependencies)
                        del self.generated_operations[app_label][0]
                    else:
                        break
                # Make a migration! Well, only if there's stuff to put in it
                if dependencies or chopped:
                    if not self.generated_operations[app_label] or chop_mode:
                        subclass = type(
                            "Migration",
                            (Migration,),
                            {"operations": [], "dependencies": []},
                        )
                        instance = subclass(
                            "auto_%i" % (len(self.migrations.get(app_label, [])) + 1),
                            app_label,
                        )
                        instance.dependencies = list(dependencies)
                        instance.operations = chopped
                        instance.initial = app_label not in self.existing_apps
                        self.migrations.setdefault(app_label, []).append(instance)
                        chop_mode = False
                    else:
                        self.generated_operations[app_label] = (
                            chopped + self.generated_operations[app_label]
                        )
            new_num_ops = sum(len(x) for x in self.generated_operations.values())
            if new_num_ops == num_ops:
                if not chop_mode:
                    chop_mode = True
                else:
                    raise ValueError(
                        "Cannot resolve operation dependencies: %r"
                        % self.generated_operations
                    )
            num_ops = new_num_ops