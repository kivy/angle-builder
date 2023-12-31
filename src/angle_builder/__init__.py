from importlib.metadata import PackageNotFoundError, version

try:
    dist_name = "angle-builder"
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError
