# Copyright 2017 Itamar Ostricher

"""Cache module, providing persistent caching decorator."""

from functools import wraps
import json
from os.path import join
import shelve


def cached(func):
  """Decorator for persistent caching of function result by its arguments."""
  shelve_file = join('.cache', func.__name__)

  @wraps(func)
  def wrapper(*args, **kwargs):
    key = json.dumps({'__args__': args, **kwargs}, sort_keys=True)
    with shelve.open(shelve_file) as cache:
      try:
        return cache[key]
      except KeyError:
        cache[key] = result = func(*args, **kwargs)
        return result

  return wrapper
