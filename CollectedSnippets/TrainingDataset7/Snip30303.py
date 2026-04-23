def test_permissions_created(self):
        from django.contrib.auth.models import Permission

        Permission.objects.get(name="May display users information")