def lookups(self, request, model_admin):
        return sorted(
            {
                (
                    employee.department.id,  # Intentionally not a string (Refs #19318)
                    employee.department.code,
                )
                for employee in model_admin.get_queryset(request)
            }
        )