def test_abstract_filefield_model(self):
        """
        FileField.model returns the concrete model for fields defined in an
        abstract model.
        """

        class AbstractMyDocument(models.Model):
            myfile = models.FileField(upload_to="unused")

            class Meta:
                abstract = True

        class MyDocument(AbstractMyDocument):
            pass

        document = MyDocument(myfile="test_file.py")
        self.assertEqual(document.myfile.field.model, MyDocument)