from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("GOSTurban")
except PackageNotFoundError:
    # package is not installed
    pass
