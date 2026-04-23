def create_initial_data(models, schema_editor):
            Article = models.get_model("test_article", "Article")
            Blog = models.get_model("test_blog", "Blog")
            blog = Blog.objects.create(name="web development done right")
            Article.objects.create(name="Frameworks", blog=blog)
            Article.objects.create(name="Programming Languages", blog=blog)