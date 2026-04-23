def num_nodes():
            plan = set(loader.graph.forwards_plan(("migrations", "7_auto")))
            return len(plan - loader.applied_migrations.keys())