def test_lookup_allowed_onetoone(self):
        class Department(models.Model):
            code = models.CharField(max_length=4, unique=True)

        class Employee(models.Model):
            department = models.ForeignKey(Department, models.CASCADE, to_field="code")

        class EmployeeProfile(models.Model):
            employee = models.OneToOneField(Employee, models.CASCADE)

        class EmployeeInfo(models.Model):
            employee = models.OneToOneField(Employee, models.CASCADE)
            description = models.CharField(max_length=100)

        class EmployeeProfileAdmin(ModelAdmin):
            list_filter = [
                "employee__employeeinfo__description",
                "employee__department__code",
            ]

        ma = EmployeeProfileAdmin(EmployeeProfile, self.site)
        # Reverse OneToOneField
        self.assertIs(
            ma.lookup_allowed(
                "employee__employeeinfo__description", "test_value", request
            ),
            True,
        )
        # OneToOneField and ForeignKey
        self.assertIs(
            ma.lookup_allowed("employee__department__code", "test_value", request),
            True,
        )