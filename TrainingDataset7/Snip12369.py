def clean_savepoints(using=None):
    """
    Reset the counter used to generate unique savepoint ids in this thread.
    """
    get_connection(using).clean_savepoints()