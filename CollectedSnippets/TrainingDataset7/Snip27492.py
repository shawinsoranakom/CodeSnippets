def create_big_data(models, schema_editor):
            Article = models.get_model("test_article", "Article")
            Blog = models.get_model("test_blog", "Blog")
            blog2 = Blog.objects.create(name="Frameworks", id=target_value)
            Article.objects.create(name="Django", blog=blog2)
            Article.objects.create(id=target_value, name="Django2", blog=blog2)