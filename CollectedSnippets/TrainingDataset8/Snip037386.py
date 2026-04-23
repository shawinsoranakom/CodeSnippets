def id_transform(data) -> Dict[str, str]:
        """Altair data transformer that returns a fake named dataset with the
        object id."""
        datasets[id(data)] = data
        return {"name": str(id(data))}