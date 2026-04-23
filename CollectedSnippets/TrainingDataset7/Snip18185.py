def forwards(apps, schema_editor):
            UserModel = apps.get_model("auth", "User")
            user = UserModel.objects.create_user("user1", password="secure")
            self.assertIsInstance(user, UserModel)