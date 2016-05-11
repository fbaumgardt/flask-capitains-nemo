import os.path as op
from collections import OrderedDict


def resource_qualifier(resource):
    """ Split a resource in (filename, directory) tuple with taking care of external resources

    :param resource: A file path or a URI
    :return: (Filename, Directory) for files, (URI, None) for URI
    """
    if resource.startswith("//") or resource.startswith("http"):
        return resource, None
    else:
        return reversed(op.split(resource))

ASSETS_STRUCTURE = {
    "js": OrderedDict(),
    "css": OrderedDict(),
    "static": OrderedDict()
}