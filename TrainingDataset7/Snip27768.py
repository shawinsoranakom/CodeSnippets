def upload_to_with_date(instance, filename):
    return f"{instance.created_at.year}/{filename}"