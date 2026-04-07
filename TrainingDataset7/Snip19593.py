def test_save_default_pk_set(self):
        post = Post.objects.create()
        with self.assertRaises(IntegrityError):
            Post(tenant_id=post.tenant_id, id=post.id).save()