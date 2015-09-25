# -*- coding: utf-8 -*-
"""
    Capitains Nemo
    ====

    Extensions for Flask to propose a Nemo extensions
"""

__version__ = "0.0.1"

import os.path as op
from flask import request, render_template, Blueprint, abort, Markup
import MyCapytain.endpoints.cts5
import MyCapytain.resources.texts.tei
import MyCapytain.resources.texts.api
import MyCapytain.resources.inventory
from lxml import etree
import requests_cache


class Nemo(object):
    ROUTES = [
        ("/", "r_index", ["GET"]),
        ("/read/<collection>", "r_collection", ["GET"]),
        ("/read/<collection>/<textgroup>", "r_texts", ["GET"]),
        ("/read/<collection>/<textgroup>/<work>/<version>", "r_version", ["GET"]),
        ("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>", "r_text", ["GET"])
    ]
    TEMPLATES = {
        "container": "container.html",
        "menu": "menu.html",
        "text": "text.html",
        "textgroups": "textgroups.html",
        "index": "index.html",
        "texts": "texts.html",
        "version": "version.html"
    }
    COLLECTIONS = {
        "latinLit": "Latin",
        "greekLit": "Ancient Greek",
        "froLit": "Medieval French"
    }
    """ Nemo is an extension for Flask python micro-framework which provides
    a User Interface to your app for dealing with CTS API.

    :param app: Flask application
    :type app: Flask
    :param api_url: URL of the API Endpoint
    :type api_url: str
    :param base_url: Base URL to use when registering the endpoint
    :type base_url: str
    :param cache: SQLITE cache file name
    :type base_url: str
    :param expire: TIme before expiration of cache, default 3600
    :type exipre: int
    :param template_folder: Folder in which the templates can be found
    :type template_folder: str
    :param static_folder: Folder in which statics file can be found
    :type static_folder: str
    :param static_url_path: Base url to use for assets
    :type static_url_path: str
    :param urls: Function and routes to register (See Nemo.ROUTES)
    :type urls: [(str, str, [str])]
    :param inventory: Default inventory to use
    :type inventory: str
    :param xslt: Wether to use the default xslt or a given xslt to transform getPassage results
    :type xslt: bool|str
    :param chunker: Dictionary of function to group responses of GetValidReff
    :type chunker: {str: function(str, function(int))}
    """

    def __init__(self, app=None, api_url="/", base_url="/nemo", cache=None, expire=3600,
                 template_folder=None, static_folder=None, static_url_path=None,
                 urls=None, inventory=None, xslt=None, chunker=None):
        __doc__ = Nemo.__doc__
        self.prefix = base_url
        self.api_url = api_url
        self.endpoint = MyCapytain.endpoints.cts5.CTS(self.api_url)
        self.templates = Nemo.TEMPLATES
        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

        self.api_url = ""
        self.api_inventory = inventory
        if self.api_inventory:
            self.endpoint.inventory = self.api_inventory
        self.cache = None
        if cache is not None:
            self.__register_cache(cache, expire)

        if template_folder:
            self.template_folder = template_folder
        else:
            self.template_folder = op.join('data', 'templates')

        if static_folder:
            self.static_folder = static_folder
        else:
            self.static_folder = op.join('data', 'static')

        if static_url_path:
            self.static_url_path = static_url_path
        else:
            self.static_url_path = "/assets/nemo"
        self.blueprint = None

        if urls:
            self._urls = urls
        else:
            self._urls = Nemo.ROUTES

        self._filters = [
            "f_active_link",
            "f_collection_i18n",
            "f_formatting_passage_reference"
        ]
        # Reusing self._inventory across requests
        self._inventory = None
        self.xslt = None

        if xslt is True:
            xml = etree.parse(op.join("data", "epidoc", "full.xsl"))
            self.xslt =etree.XSLT(xml)
        elif self.xslt:
            xml = etree.parse(xslt)
            self.xslt =etree.XSLT(xml)

        self.chunker = {}
        self.chunker["default"] = Nemo.default_chunker
        if isinstance(chunker, dict):
            self.chunker.update(chunker)

    def __register_cache(self, sqlite_path, expire):
        """ Set up a request cache

        :param sqlite_path: Set up a sqlite cache system
        :type sqlite_path: str
        :param expire: Time for the cache to expire
        :type expire: int
        """
        self.cache = requests_cache.install_cache(
            sqlite_path,
            backend="sqlite",
            expire_after=expire
        )

    def init_app(self, app):
        """ Initiate the application

        :param app: Flask application on which to add the extension
        :type app: flask.Flask
        """
        if "CTS_API_URL" in app.config:
            self.api_url = app.config['CTS_API_URL']
        if "CTS_API_INVENTORY" in app.config:
            self.api_inventory = app.config['CTS_API_INVENTORY']
        if self.app is None:
            self.app = app

    def get_inventory(self):
        """ Request the api endpoint to retrieve information about the inventory

        :return: The text inventory
        :rtype: MyCapytain.resources.inventory.TextInventory
        """
        if self._inventory:
            return self._inventory

        reply = self.endpoint.getCapabilities(inventory=self.api_inventory)
        inventory = MyCapytain.resources.inventory.TextInventory(resource=reply)
        self._inventory = inventory
        return self._inventory

    def get_collections(self):
        """ Filter inventory and make a list of available collections

        :return: A set of CTS Namespaces
        :rtype: set(str)
        """
        inventory = self.get_inventory()
        urns = set(
            [inventory.textgroups[textgroup].urn[2] for textgroup in inventory.textgroups]
        )
        return urns

    def get_textgroups(self, collection_urn=None):
        """ Retrieve textgroups

        :param collection_urn: Collection to use for filtering the textgroups
        :type collection_urn: str
        :return: List of textgroup filtered by collection
        :rtype: [MyCapytain.resources.inventory.Textgroup]
        """
        inventory = self.get_inventory()
        if collection_urn is not None:
            return Nemo.map_urns(inventory, collection_urn, 2, "textgroups")
        return list(inventory.textgroups.values())

    def get_works(self, collection_urn=None, textgroup_urn=None):
        """ Retrieve works

        :param collection_urn: Collection to use for filtering the textgroups
        :type collection_urn: str
        :param textgroup_urn: Textgroup to use for filtering the works
        :type textgroup_urn: str
        :return: List of work filtered by collection/Textgroup
        :rtype: [MyCapytain.resources.inventory.Work]
        """
        if collection_urn is not None and textgroup_urn is not None:
            textgroup = list(
                filter(lambda x: Nemo.filter_urn(x, 3, textgroup_urn), self.get_textgroups(collection_urn))
            )
            if len(textgroup) == 1:
                return textgroup[0].works.values()
            else:
                return []
        elif collection_urn is None and textgroup_urn is None:
            return [work for textgroup in self.get_inventory().textgroups.values() for work in textgroup.works.values()]
        else:
            raise ValueError("Get_Work takes either two None value or two set up value")

    def get_texts(self, collection_urn=None, textgroup_urn=None, work_urn=None):
        """ Retrieve texts

        :param collection_urn: Collection to use for filtering the textgroups
        :type collection_urn: str
        :param textgroup_urn: Textgroup to use for filtering the works
        :type textgroup_urn: str
        :param work_urn: Work to use for filtering the texts
        :type work_urn: str
        :return: List of texts filtered by parameters
        :rtype: [MyCapytain.resources.inventory.Text]
        """
        if collection_urn is not None and textgroup_urn is not None and work_urn is not None:
            work = list(
                filter(lambda x: Nemo.filter_urn(x, 4, work_urn), self.get_works(collection_urn, textgroup_urn))
            )
            if len(work) == 1:
                return work[0].texts.values()
            else:
                return []
        elif collection_urn is not None and textgroup_urn is not None and work_urn is None:
            return [
                text
                for work in self.get_works(collection_urn, textgroup_urn)
                for text in work.texts.values()
            ]
        elif collection_urn is None and textgroup_urn is None and work_urn is None:
            return [
                text
                for textgroup in self.get_inventory().textgroups.values()
                for work in textgroup.works.values()
                for text in work.texts.values()
            ]
        else:
            raise ValueError("Get_Work takes either two None value or two set up value")

    def get_text(self, collection_urn, textgroup_urn, work_urn, version_urn):
        """ Retrieve one version of a Text

        :param collection_urn: Collection to use for filtering the textgroups
        :type collection_urn: str
        :param textgroup_urn: Textgroup to use for filtering the works
        :type textgroup_urn: str
        :param work_urn: Work identifier to use for filtering texts
        :type work_urn: str
        :param version_urn: Version identifier
        :type version_urn: str
        :return: A Text represented by the various parameters
        :rtype: MyCapytain.resources.inventory.Text
        """
        work = list(
            filter(lambda x: Nemo.filter_urn(x, 4, work_urn), self.get_works(collection_urn, textgroup_urn))
        )
        if len(work) == 1:
            texts = work[0].texts.values()
        else:
            texts = []

        texts = [text for text in texts if text.urn[5] == version_urn]
        if len(texts) == 1:
            return texts[0]
        abort(404)

    def get_reffs(self, collection, textgroup, work, version):
        """ Get the setup for valid reffs.

        Returns the inventory text object with its metadata and a callback function taking a level parameter
        and returning a list of strings.

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :return: Text with its metadata, callback function to retrieve validreffs
        :rtype: (MyCapytains.resources.texts.api.Text, lambda: [str])
        """
        text = self.get_text(collection, textgroup, work, version)
        reffs = MyCapytain.resources.texts.api.Text(
            "urn:cts:{0}:{1}.{2}.{3}".format(collection, textgroup, work, version),
            self.endpoint,
            citation=text.citation
        )
        return text, lambda level: reffs.getValidReff(level=level)

    def get_passage(self, collection, textgroup, work, version, passage_identifier):
        """ Retrieve the passage identified by the parameters


        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :param passage_identifier: Reference Identifier
        :type passage_identifier: str
        :return: A Passage object containing informations about the passage
        :rtype: MyCapytain.resources.texts.api.Passage
        """
        text = MyCapytain.resources.texts.api.Text(
            "urn:cts:{0}:{1}.{2}.{3}".format(collection, textgroup, work, version),
            self.endpoint
        )
        passage = text.getPassage(passage_identifier)
        return passage

    @staticmethod
    def map_urns(items, query, part_of_urn=1, attr="textgroups"):
        """ Small function to map urns to filter out a list of items or on a parent item

        :param items: Inventory object
        :type items: MyCapytains.resources.inventory.Resource
        :param query: Part of urn to check against
        :type query: str
        :param part_of_urn: Identifier of the part of the urn
        :type part_of_urn: int
        :return: Items corresponding to the object children filtered by the query
        :rtype: list(items.children)
        """

        if attr is not None:
            return [
                item
                for item in getattr(items, attr).values()
                if Nemo.filter_urn(item, part_of_urn, query)
            ]

    @staticmethod
    def filter_urn(item, part_of_urn, query):
        """ Small function to map urns to filter out a list of items or on a parent item

        :param item: Inventory object
        :param query: Part of urn to check against
        :type query: str
        :param part_of_urn: Identifier of the part of the urn
        :type part_of_urn: int
        :return: Items corresponding to the object children filtered by the query
        :rtype: list(items.children)
        """
        return item.urn[part_of_urn].lower() == query.lower().strip()

    def r_index(self):
        """ Homepage route function

        :return: Template to use for Home page
        :rtype: {str: str}
        """
        return {"template": self.templates["index"]}

    def r_collection(self, collection):
        """ Collection content browsing route function

        :param collection: Collection identifier
        :type collection: str
        :return: Template and textgroups contained in given collections
        :rtype: {str: Any}
        """
        return {
            "template": self.templates["textgroups"],
            "textgroups": self.get_textgroups(collection)
        }

    def r_texts(self, collection, textgroup):
        """ Textgroup content browsing route function

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup Identifier
        :type textgroup: str
        :return: Template and texts contained in given textgroup
        :rtype: {str: Any}
        """
        return {
            "template": self.templates["texts"],
            "texts": self.get_texts(collection, textgroup)
        }

    def r_version(self, collection, textgroup, work, version):
        """ Text exemplar references browsing route function

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup Identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :return: Template, version inventory object and references urn parts
        :rtype: {
            "template" : str,
            "version": MyCapytains.resources.inventory.Text,
            "reffs": [str]
            }
        """
        version, reffs = self.get_reffs(collection, textgroup, work, version)
        reffs = self.chunk(version, reffs)
        return {
            "template": self.templates["version"],
            "version": version,
            "reffs": reffs
        }

    def r_text(self, collection, textgroup, work, version, passage_identifier):
        """ Retrieve the text of the passage

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup Identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :param passage_identifier: Reference identifier
        :type passage_identifier: str
        :return: Template, version inventory object and Markup object representing the text
        :rtype: {str: Any}

        ..todo:: Change text_passage to keep being lxml and make so self.render turn etree element to Markup.
        """
        text = self.get_passage(collection, textgroup, work, version, passage_identifier)
        if self.xslt:
            passage = etree.tostring(self.xslt(text.xml))
        else:
            passage = etree.tostring(text.xml, encoding=str)

        version = self.get_text(collection, textgroup, work, version)
        return {
            "template": self.templates["text"],
            "version": version,
            "text_passage": Markup(passage)
        }

    def create_blueprint(self):
        """ Create blueprint and register rules

        :return: Blueprint of the current nemo app
        :rtype: flask.Blueprint
        """
        self.blueprint = Blueprint(
            "nemo",
            "nemo",
            url_prefix=self.prefix,
            template_folder=self.template_folder,
            static_folder=self.static_folder,
            static_url_path=self.static_url_path
        )

        for url, name, methods in self._urls:
            self.blueprint.add_url_rule(
                url,
                view_func=self.view_maker(name),
                endpoint=name,
                methods=methods
            )

        return self.blueprint

    def view_maker(self, name):
        """ Create a view

        :param name: Name of the route function to use for the view.
        :type name: str
        :return: Route function which makes use of Nemo context (such as menu informations)
        :rtype: function
        """
        return lambda **kwargs: self.route(getattr(self, name), **kwargs)

    def render(self, template, **kwargs):
        """ Render a route template and adds information to this route.

        :param template: Template name
        :type template: str
        :param kwargs: dictionary of named arguments used to be passed to the template
        :type kwargs: dict
        :return: Http Response with rendered template
        :rtype: flask.Response
        """
        kwargs["collections"] = self.get_collections()
        kwargs["lang"] = "eng"

        if Nemo.in_and_not_int("textgroup", "textgroups", kwargs):
            kwargs["textgroups"] = self.get_textgroups(kwargs["url"]["collection"])

            if Nemo.in_and_not_int("text", "texts", kwargs):
                kwargs["texts"] = self.get_texts(kwargs["url"]["collection"], kwargs["url"]["textgroup"])

        return render_template(template, **kwargs)

    def route(self, fn, **kwargs):
        """ Route helper : apply fn function but keep the calling object, *ie* kwargs, for other functions

        :param fn: Function to run the route with
        :type fn: function
        :param kwargs: Parsed url arguments
        :type kwargs: dict
        :return: HTTP Response with rendered template
        :rtype: flask.Response
        """
        new_kwargs = fn(**kwargs)
        new_kwargs["url"] = kwargs
        return self.render(**new_kwargs)

    def register_routes(self):
        """ Register routes on app using Blueprint

        :return: Nemo blueprint
        :rtype: flask.Blueprint
        """
        if self.app is not None:
            blueprint = self.create_blueprint()
            self.app.register_blueprint(blueprint)
            return blueprint
        return None

    def register_filters(self):
        """ Register filters for Jinja to use

       ..note::  Extends the dictionary filters of jinja_env using self._filters list
        """
        for _filter in self._filters:
            self.app.jinja_env.filters[
                _filter.replace("f_", "")
            ] = getattr(self.__class__, _filter)

    def chunk(self, text, reffs):
        """ Handle a list of references depending on the text identifier using the chunker dictionary.

        :param text: Text object from which comes the references
        :type text: MyCapytains.resources.texts.api.Text
        :param reffs: Callback function to retrieve a list of string with a level parameter
        :type reffs: callback(level)
        :return: Transformed list of references
        :rtype: [str]
        """
        if str(text.urn) in self.chunker:
            return self.chunker[str(text.urn)](text, reffs)
        return self.chunker["default"](text, reffs)

    @staticmethod
    def in_and_not_int(identifier, collection, kwargs):
        """ Check if an element identified by identifier is in kwargs but not the collection containing it

        :param identifier: URL Identifier of one kind of element (Textgroup, work, etc.)
        :type identifier: str
        :param collection: Resource identifier of one kind of element (Textgroup, work, etc.)
        :type collection: str
        :param kwargs: Arguments passed to a template
        :type kwargs: {str: Any}
        :return: Indicator of presence of required informations
        :rtype: bool
        """
        return identifier in kwargs["url"] and collection not in kwargs

    @staticmethod
    def f_active_link(string):
        """ Check if current string is in the list of names

        :param string: String to check for in url
        :return: CSS class "active" if valid
        :rtype: str
        """
        if string in request.path:
            return "active"
        return ""

    @staticmethod
    def f_collection_i18n(string):
        """ Return a i18n human readable version of a CTS domain such as latinLit

        :param string: CTS Domain identifier
        :type string: str
        :return: Human i18n readable version of the CTS Domain
        :rtype: str
        """
        if string in Nemo.COLLECTIONS:
            return Nemo.COLLECTIONS[string]
        return string

    @staticmethod
    def f_formatting_passage_reference(string):
        """ Get the first part only of a two parts reference

        :param string: A urn reference part
        :type string: str
        :return: First part only of the two parts reference
        :rtype: str
        """
        return string.split("-")[0]

    @staticmethod
    def default_chunker(text, getreffs):
        """ This is the default chunker which will resolve the reference giving a callback (getreffs) and a text object with its metadata

        :param text: Text Object representing either an edition or a translation
        :type text: MyCapytains.resources.inventory.Text
        :param getreffs: callback function which retrieves a list of references
        :type getreffs: function

        :return: List of urn references with their human readable version
        :rtype: [(str, str)]
        """
        level = len(text.citation)
        return [tuple([reff.split(":")[-1]]*2) for reff in getreffs(level=level)]

    @staticmethod
    def scheme_chunker(text, getreffs):
        """ This is the scheme chunker which will resolve the reference giving a callback (getreffs) and a text object with its metadata

        :param text: Text Object representing either an edition or a translation
        :type text: MyCapytains.resources.inventory.Text
        :param getreffs: callback function which retrieves a list of references
        :type getreffs: function

        :return: List of urn references with their human readable version
        :rtype: [(str, str)]
        """
        # print(text)
        level = len(text.citation)
        types = [citation.name for citation in text.citation]
        if types == ["book", "poem", "line"]:
            level = 2
        elif types == ["book", "lines"]:
            return Nemo.line_chunker(text, getreffs)
        return [tuple([reff.split(":")[-1]]*2) for reff in getreffs(level=level)]

    @staticmethod
    def line_chunker(text, getreffs, lines=30):
        """ Groups line reference together

        :param text: Text object
        :type text: MyCapytains.resources.text.api
        :param getreffs: Callback function to retrieve text
        :type getreffs: function(level)
        :param lines: Number of lines to use by group
        :type lines: int
        :return: List of grouped urn references with their human readable version
        :rtype: [(str, str)]
        """
        level = len(text.citation)
        source_reffs = [reff.split(":")[-1] for reff in getreffs(level=level)]
        reffs = []
        i = 0
        while i + lines - 1 < len(source_reffs):
            reffs.append(tuple(source_reffs[i]+"-"+source_reffs[i+lines-1], source_reffs[i]))
            i += lines
        return reffs