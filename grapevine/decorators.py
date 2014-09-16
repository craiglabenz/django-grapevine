from __future__ import unicode_literals


def smoosh_args(*args, **kwargs):
    key_suffix = ''
    prepared_args = []
    prepared_kwargs = []
    for arg in args:
        prepared_args.append(str(arg))

    for key, value in kwargs.items():
        prepared_kwargs.append('%s=%s' % (key, str(value),))

    all_prepared_args = prepared_args + prepared_kwargs
    if all_prepared_args:
        key_suffix = ';'.join(all_prepared_args)

    return key_suffix


def memoize(fnc):
    """
    Decorator that accepts a variable name at which to cache the results
    of this function. Now honoring parameters!

    Usage:

        class SomeClass(object):
            @memoize
            def get_title(self):
                print "doing work!"
                return "Jurassic Park"

            @property
            @memoize
            def favorite_trilogy(self):
                print "doing property work!"
                return "Star Wars"


        >>> my_obj = SomeClass()
        >>> my_obj.get_title()
        >>> doing work!
        >>> "Jurassic Park"
        >>>
        >>> my_obj.get_title()
        >>> "Jurassic Park"
        >>>
        >>> my_obj.favorite_trilogy
        >>> doing property work!
        >>> "Star Wars"
        >>>
        >>> my_obj.favorite_trilogy
        >>> "Star Wars"

    """
    def wrapper(self, *args, **kwargs):
        # Make sure the memoize cache
        if not hasattr(self, '_memoize_cache'):
            self._memoize_cache = {}

        cache_attr_name = fnc.__name__
        self._memoize_cache.setdefault(cache_attr_name, {})

        key_suffix = smoosh_args(*args, **kwargs)

        try:
            # Hope for a cache hit
            return self._memoize_cache[cache_attr_name][key_suffix]
        except KeyError:
            self._memoize_cache[cache_attr_name][key_suffix] = None

        # Calculate the value
        val = fnc(self, *args, **kwargs)

        # Save it for later
        self._memoize_cache[cache_attr_name][key_suffix] = val
        return val

    return wrapper
