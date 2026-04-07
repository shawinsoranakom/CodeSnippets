def _generate_plan(self, nodes, at_end):
        plan = OrderedSet()
        for node in nodes:
            for migration in self.forwards_plan(node):
                if migration not in plan and (at_end or migration not in nodes):
                    plan.add(migration)
        return list(plan)