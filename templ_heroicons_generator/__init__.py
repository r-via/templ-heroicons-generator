# templ_heroicons_generator/__init__.py
try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("templ-heroicons-generator")
    except PackageNotFoundError:

        __version__ = "0.0.0-dev"
except ImportError:
    # Pour Python < 3.8, ou si importlib_metadata (backport) n'est pas là
    __version__ = "0.0.0-dev"