import json

def check_for_dunder(default):
    def checker(o):
        try:
            return o.__json__()
        except AttributeError:
            if default is not None:
                return default
            else:
                raise TypeError(f"{o} is not JSON Serializable")

    return checker

def dumps(*args, **kwargs):
    kwargs['default'] = check_for_dunder(kwargs.get('default'))
    return json.dumps(*args, **kwargs)