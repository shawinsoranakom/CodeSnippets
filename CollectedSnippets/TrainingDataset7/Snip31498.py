def test_creation_with_db_table_double_quotes(self):
        oracle_user = connection.creation._test_database_user()

        class Student(Model):
            name = CharField(max_length=30)

            class Meta:
                app_label = "schema"
                apps = new_apps
                db_table = '"%s"."DJANGO_STUDENT_TABLE"' % oracle_user

        class Document(Model):
            name = CharField(max_length=30)
            students = ManyToManyField(Student)

            class Meta:
                app_label = "schema"
                apps = new_apps
                db_table = '"%s"."DJANGO_DOCUMENT_TABLE"' % oracle_user

        self.isolated_local_models = [Student, Document]

        with connection.schema_editor() as editor:
            editor.create_model(Student)
            editor.create_model(Document)

        doc = Document.objects.create(name="Test Name")
        student = Student.objects.create(name="Some man")
        doc.students.add(student)