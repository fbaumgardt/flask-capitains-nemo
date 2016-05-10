from flask import Flask
from unittest import TestCase
from flask_nemo import Nemo
from flask_nemo.plugin import PluginPrototype
from tests.resources import NautilusDummy


class PluginRoute(PluginPrototype):
    ROUTES = [
        ("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>/<visavis>", "r_double", ["GET"])
    ]

    TEMPLATES = {
        "r_double": "examples/translations/r_double.html"
    }

    def r_double(self, collection, textgroup, work, version, passage_identifier, visavis):
        args = self.nemo.r_passage(collection, textgroup, work, version, passage_identifier)
        # Call with other identifiers and add "visavis_" front of the argument
        args.update({
            "visavis_{0}".format(key): value for key, value in self.nemo.r_passage(
                collection, textgroup, work, visavis, passage_identifier
            ).items()
        })
        args["template"] = self.templates["r_double"]
        return args


class PluginClearRoute(PluginRoute):
    CLEAR = True

    TEMPLATES = {
        "r_double": "tests/test_data/r_double.html"
    }


class TestPluginRoutes(TestCase):
    """ Test plugin implementation of filters
    """

    def setUp(self):
        app = Flask("Nemo")
        app.debug = True
        self.plugin_normal = PluginRoute(name="normal")
        self.plugin_namespacing = PluginRoute(name="test", namespacing=True)
        self.plugin_autonamespacing = PluginRoute(namespacing=True)
        nemo = Nemo(
            app=app,
            base_url="",
            retriever=NautilusDummy,
            chunker={"default": lambda x, y: Nemo.level_grouper(x, y, groupby=30)},
            plugins=[self.plugin_normal, self.plugin_namespacing, self.plugin_autonamespacing]
        )

        self.client = app.test_client()

    def test_page_works(self):
        """ Test that passage page contains what is relevant : text and next passages"""
        query_data = str(self.client.get("/read/farsiLit/hafez/divan/perseus-eng1/1.1/perseus-ger1").data)
        self.assertIn(
            'Ho ! Saki, pass around and offer the bowl (of love for God)', query_data,
            "English text should be displayed"
        )
        self.assertIn(
            'Finstere Schatten der Nacht!', query_data,
            "German text should be displayed"
        )

    def test_plugin_clear(self):
        """ Test that passage page contains what is relevant : text and next passages"""

        app = Flask("Nemo")
        app.debug = True
        plugin = PluginClearRoute(name="normal")
        nemo = Nemo(
            app=app,
            base_url="",
            retriever=NautilusDummy,
            chunker={"default": lambda x, y: Nemo.level_grouper(x, y, groupby=30)},
            plugins=[plugin]
        )

        client = app.test_client()
        req = client.get("/read/farsiLit/hafez/divan/perseus-eng1/1.1")
        self.assertEqual(
            404, req.status_code,
            "Original routes should not exist anymore"
        )
        query_data = str(client.get("/read/farsiLit/hafez/divan/perseus-eng1/1.1/perseus-ger1").data)
        self.assertIn(
            'Ho ! Saki, pass around and offer the bowl (of love for God)', query_data,
            "English text should be displayed"
        )
        self.assertIn(
            'Finstere Schatten der Nacht!', query_data,
            "German text should be displayed"
        )
