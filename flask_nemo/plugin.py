# -*- coding: utf-8 -*-

from copy import copy

class PluginPrototype(object):
    """ Prototype for Nemo Plugins

    :param name: Name of the instance of the plugins. Defaults to the class name
    :param nemo: Instance of Nemo
    :param namespacing: Automatically overwrites the route

    :cvar ROUTES: Routes represents the routes to be added to the Nemo instance. They take the form of a 3-tuple such as `("/read/<collection>", "r_collection", ["GET"])`
    :type ROUTES: list
    :cvar TEMPLATES: Dictionaries of template names and html file names
    :type TEMPLATES: dict
    :cvar FILTERS: List of filters to register. Naming convention is f_doSomething
    :type FILTERS: list
    :cvar AUGMENT_RENDER: Enables post-processing in view rendering function Nemo().render(template, **kwargs)
    :type AUGMENT_RENDER: bool

    :ivar templates: Instance-specific dictionary of templates
    :ivar routes: Instance-specific list of routes
    :ivar filters: Instance-specific list of filters
    :ivar augment: Instance-specific status of presence of post-processing function (General view information)

    :Example:
    .. code-block:: python

        ROUTES = [
            # (Path like flask, Name of the function (convention is r_*), List of Http Methods)
            ("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>/<visavis>", "r_double", ["GET"])
        ]

    :ivar name: Name of the plugin instance

    """
    ROUTES = []
    TEMPLATES = {}
    FILTERS = []
    HAS_AUGMENT_RENDER = True

    def __init__(self, name=None, nemo=None, namespacing=False, *args, **kwargs):
        self.__nemo__ = None
        self.__instance_name__ = name

        if not name:
            self.__instance_name__ = type(self).__name__

        self.__routes__ = copy(type(self).ROUTES)
        self.__filters__ = copy(type(self).FILTERS)
        self.__templates__ = copy(type(self).TEMPLATES)
        self.__augment__ = copy(type(self).HAS_AUGMENT_RENDER)

        if namespacing:
            for i in range(0, len(self.__routes__)):
                self.__routes__[i] = tuple(
                    ["/{0}{1}".format(self.name, self.__routes__[i][0])] + self.__routes__[i][1:]
                )

            for i in range(0, len(self.__filters__)):
                self.__filters__[i] = "f_{}_{}".format(self.name, self.__filters__[i][2:])

        if nemo:
            self.register_nemo(nemo)

    def register_nemo(self, nemo=None):
        """ Register Nemo on to the plugin instance

        :param nemo: Instance of Nemo
        """
        self.__nemo__ = nemo

    @property
    def augment(self):
        return self.__augment__

    @property
    def name(self):
        return self.__instance_name__

    @property
    def routes(self):
        return self.__routes__

    @property
    def filters(self):
        return self.__filters__

    @property
    def templates(self):
        return self.__templates__

    def render(self, kwargs):
        """ View Rendering function that gets triggered before nemo renders the resources and adds informations to \
        pass to the templates

        :param kwargs: Dictionary of arguments to pass to the template
        :return: Dictionary of arguments to pass to the template
        """
        return kwargs