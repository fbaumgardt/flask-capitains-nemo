Nemo Plugin System
==================

Since flask-capitains-nemo 1.0.0, plugins are a reality. They bring a much easy way to stack new functionalities in Nemo and provide large reusability and modularity to everyone.

Design
######

Nemo Plugins are quite close in design to the Nemo object but differ in a major way : they do not have any Flask Blueprint instance and are not aware directly of the flask object. They only serve as a simple and efficient way to plugin in Nemo a set of resources, from routes to assets as well as filters.

The way Nemo deals with plugins is based on a stack design. Each plugin is inserted one after the other and they take effect this way. The last plugin routes for the main route `/` is always the one showed up, as it is for assets and templates namespaces.

The major properties of plugins are - and should be - class variables and copied during initiation to ensure a strong structure.