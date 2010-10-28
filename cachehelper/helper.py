import re

import string
import random
import inspect
import functools
import threading

from django.db import models
from django.core.cache import cache

_format_re = re.compile('%[^%]')

__all__ = ('cachelib',)

class CacheLibrary(threading.local):
    cache_keys = None
    chars = string.lowercase + string.uppercase
    cache_version = 1

    def __init__(self):
        self.cache_keys = {}

    def _rand_string(self, length):
        return ''.join(random.choice(chars) for _ in range(length))

    def compute_arity(self, format):
        return len(_format_re.split(format)) - 1

    

    def invalidate(self, obj):
        model = type(obj)
        prefix = '%s_%s_%s_' % (CacheLibrary.cache_version, model.__name__, obj.pk)
        for template, arity, method, cache_timeout, recompute in self.cache_keys.get(model.__name__, ()):
            if arity == 0:
                cache.delete(prefix + template)
            else:
                cache.delete(prefix + template % (('_',) * arity))

    def recalculate(self, obj):
        self.invalidate(obj)
        model = type(obj)
        prefix = '%s_%s_%s_' % (CacheLibrary.cache_version, model.__name__, obj.pk)
        for template, arity, method, cache_timeout, recompute in self.cache_keys.get(model.__name__, ()):
            if arity == 0 and recompute:
                result = method(obj)
                if result is not None:
                    cache.set(prefix + template, result, cache_timeout)

    def register_cache(self, cache_key_template, cache_timeout=86400, model=None, skip_pos=0, recompute=True):
        def _decorator(method):
            if model is not None:
                if isinstance(model, type):
                    model_name = model.__name__
                else:
                    model_name = model
            else:
                model_name = inspect.getouterframes(inspect.currentframe())[1][3]
            if model_name not in self.cache_keys:
                self.cache_keys[model_name] = []
            arity = self.compute_arity(cache_key_template)
            self.cache_keys[model_name].append((cache_key_template, 
                                                arity,
                                                method,
                                                cache_timeout,
                                                recompute,
                                                ))

            @functools.wraps(method)
            def _arity_zero(*args, **kwargs):
                obj = args[skip_pos]
                if isinstance(obj, models.Model):
                    pk = obj.pk
                else:
                    pk = obj
                prefix = '%s_%s_%s_' % (CacheLibrary.cache_version, model_name, pk)
                key = prefix + cache_key_template
                result = cache.get(key)
                if result is None:
                    result = method(*args, **kwargs)
                    if result is not None:
                        cache.set(key, result, cache_timeout)
                return result
            if not arity:
                return _arity_zero

            @functools.wraps(method)
            def _arity_nonzero(*args, **kwargs):
                obj = args[skip_pos]
                if isinstance(obj, models.Model):
                    pk = obj.pk
                else:
                    pk = obj
                prefix = '%s_%s_%s_' % (CacheLibrary.cache_version, model_name, pk)
                outer_key = prefix + cache_key_template % (('_',) * arity)
                inner_key_val = cache.get(outer_key)
                if inner_key_val is None:
                    inner_key_val = self._rand_string(5)
                    cache.set(outer_key, inner_key_val, 86400 * 30)
                key = '_'.join((prefix, inner_key_val, cache_key_template % tuple(args[skip_pos:arity])))
                result = cache.get(key)
                if result is None:
                    result = method(*args, **kwargs)
                    if result is not None:
                        cache.set(key, result, cache_timeout)
                return result
            return _arity_nonzero
        return _decorator

cachelib = CacheLibrary()
