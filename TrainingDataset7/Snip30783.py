def test_nested_in_subquery(self):
        extra = ExtraInfo.objects.create()
        author = Author.objects.create(num=42, extra=extra)
        report = Report.objects.create(creator=author)
        comment = ReportComment.objects.create(report=report)
        comments = ReportComment.objects.filter(
            report__in=Report.objects.filter(
                creator__in=extra.author_set.all(),
            ),
        )
        self.assertSequenceEqual(comments, [comment])