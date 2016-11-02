from flask import Flask
from flask.ext.nemo import Nemo
from flask_nemo.chunker import default_chunker as __default_chunker__, level_grouper as __level_grouper__, \
    scheme_chunker as __scheme_chunker__
from werkzeug.contrib.cache import SimpleCache

app = Flask(
    __name__
)

# We set up Nemo
nemo = Nemo(
    app=app,
    name="nemo",
    base_url="",
    css=None,
    inventory=None,
    api_url="http://localhost:8000/",
    chunker={
        "default": lambda x, y: __level_grouper__(x, y, groupby=25),
        "urn:cts:pdlrefwk:viaf88890045.003.perseus-eng1": __scheme_chunker__
    },
    cache=SimpleCache()
)


# We run the app
app.debug = True

app.run(port=7070)