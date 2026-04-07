def test_converter_reverse_with_second_layer_instance_namespace(self):
        kwargs = included_kwargs.copy()
        kwargs["last_value"] = b"world"
        url = reverse("instance-ns-base64:subsubpattern-base64", kwargs=kwargs)
        self.assertEqual(url, "/base64/aGVsbG8=/subpatterns/d29ybGQ=/d29ybGQ=/")