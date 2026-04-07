def test_files_content(self):
        self.assertTableNotExists("migrations_unicodemodel")
        apps.register_model("migrations", UnicodeModel)
        with self.temporary_migration_module() as migration_dir:
            call_command("makemigrations", "migrations", verbosity=0)

            # Check for empty __init__.py file in migrations folder
            init_file = os.path.join(migration_dir, "__init__.py")
            self.assertTrue(os.path.exists(init_file))

            with open(init_file) as fp:
                content = fp.read()
            self.assertEqual(content, "")

            # Check for existing 0001_initial.py file in migration folder
            initial_file = os.path.join(migration_dir, "0001_initial.py")
            self.assertTrue(os.path.exists(initial_file))

            with open(initial_file, encoding="utf-8") as fp:
                content = fp.read()
                self.assertIn("migrations.CreateModel", content)
                self.assertIn("initial = True", content)

                self.assertIn("úñí©óðé µóðéø", content)  # Meta.verbose_name
                self.assertIn("úñí©óðé µóðéøß", content)  # Meta.verbose_name_plural
                self.assertIn("ÚÑÍ¢ÓÐÉ", content)  # title.verbose_name
                self.assertIn("“Ðjáñgó”", content)