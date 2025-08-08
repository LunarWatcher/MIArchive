def meta_context(
    context: dict[str, object],
    title: str,
    description: str,
    scripts: list[str]
):
    context["Meta"] = {
        "Title": title,
        "Description": description,
        "Scripts": scripts
    }

def account_context(
    context: dict[str, object],
):
    pass
