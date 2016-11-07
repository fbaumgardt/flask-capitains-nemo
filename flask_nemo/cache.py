from werkzeug.contrib.cache import SimpleCache


class Cache(object):

    def __init__(self, cache=None):

        if cache:
            self.cache = cache
        else:
            self.cache = SimpleCache()

    def get_or_else(self, key, op, *args, **kwargs):
        cached = self.cache.get(key)
        if not cached:
            cached = op(*args, **kwargs)
            self.cache.add(key, cached)
        return cached
