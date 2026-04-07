def employ(employer, employee, title):
            Employment.objects.get_or_create(
                employee=employee, employer=employer, title=title
            )