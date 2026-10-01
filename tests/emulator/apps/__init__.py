import importlib
import os


def load_driver(name=None):
    """Load one app module without importing device or build dependencies."""
    name = (name if name is not None else os.environ.get('NOD_APP', 'termux'))
    module_name = name.replace('-', '_')
    if not module_name.isidentifier():
        raise ValueError(f'Invalid emulator app driver: {name!r}')
    return importlib.import_module(f'{__name__}.{module_name}').Driver()


app = load_driver()
