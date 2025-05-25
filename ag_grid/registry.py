AGGRID_REGISTRY = {}


def register(model):
    def decorator(aggrid_cls):
        AGGRID_REGISTRY[model] = aggrid_cls()
        return aggrid_cls

    return decorator


def get_config(model):
    return AGGRID_REGISTRY.get(model)
