def migration_plan(self, targets, clean_start=False):
        """
        Given a set of targets, return a list of (Migration instance,
        backwards?).
        """
        plan = []
        if clean_start:
            applied = {}
        else:
            applied = dict(self.loader.applied_migrations)
        for target in targets:
            # If the target is (app_label, None), that means unmigrate
            # everything
            if target[1] is None:
                for root in self.loader.graph.root_nodes():
                    if root[0] == target[0]:
                        for migration in self.loader.graph.backwards_plan(root):
                            if migration in applied:
                                plan.append((self.loader.graph.nodes[migration], True))
                                applied.pop(migration)
            # If the target is missing, it's likely a replaced migration.
            # Reload the graph without replacements.
            elif (
                self.loader.replace_migrations
                and target not in self.loader.graph.node_map
            ):
                self.loader.replace_migrations = False
                self.loader.build_graph()
                return self.migration_plan(targets, clean_start=clean_start)
            # If the migration is already applied, do backwards mode,
            # otherwise do forwards mode.
            elif target in applied:
                # Don't migrate backwards all the way to the target node (that
                # may roll back dependencies in other apps that don't need to
                # be rolled back); instead roll back through target's immediate
                # child(ren) in the same app, and no further.
                next_in_app = sorted(
                    n
                    for n in self.loader.graph.node_map[target].children
                    if n[0] == target[0]
                )
                for node in next_in_app:
                    for migration in self.loader.graph.backwards_plan(node):
                        if migration in applied:
                            plan.append((self.loader.graph.nodes[migration], True))
                            applied.pop(migration)
            else:
                for migration in self.loader.graph.forwards_plan(target):
                    if migration not in applied:
                        plan.append((self.loader.graph.nodes[migration], False))
                        applied[migration] = self.loader.graph.nodes[migration]
        return plan