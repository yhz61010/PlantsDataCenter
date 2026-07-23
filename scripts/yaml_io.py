import yaml


def dump_species(rec):
    return yaml.safe_dump(
        rec,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=4096,
    )
