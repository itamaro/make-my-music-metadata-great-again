# Copyright 2017 Itamar Ostricher

"""Music API module for accessing the LastFM Music API.

Ref: https://www.last.fm/api
"""

import json
import os

import requests

from .cache import cached
from .utils import norm_title


_API_URL = 'http://ws.audioscrobbler.com/2.0/'
_API_KEY = os.environ.get('API_KEY')


@cached
def api_call(method, **params):
  """Return JSON result of calling the LastFM API `method` with `params`."""
  if _API_KEY is None:
    raise RuntimeError('Missing API Key')
  params.update({
      'method': method,
      'api_key': _API_KEY,
      'format': 'json',
  })
  headers = {'user-agent': 'mmmmga/0.1.1'}
  response = requests.get(_API_URL, params, headers=headers)
  return response.json()


def search_album(album_name):
  """Return search results for `album_name`."""
  return api_call('album.search', album=album_name)


def get_album(artist, album):
  """Return album info object for `album` by `artist`."""
  return api_call('album.getInfo', artist=artist, album=album, autocorrect=1)


def get_album_metadata(artist, album):
  """Return a dictionary describing the `album` by `artist` metadata."""
  metadata = get_album(artist, album)['album']
  discs = []
  for track in metadata['tracks']['track']:
    track_meta = {'name': norm_title(track['name']),
                  'pos': int(track['@attr']['rank'])}
    if len(discs) == 0:
      # start first disc track list
      discs.append([track_meta])
    elif track_meta['pos'] == discs[-1][-1]['pos'] + 1:
      discs[-1].append(track_meta)
    else:
      # start new disc track list
      discs.append([track_meta])
  return {
    'artist': metadata['artist'],
    'album': norm_title(metadata['name']),
    'discs': discs,
    'images': {image['size']: image['#text'] for image in metadata['image']},
    # 'published': parse(metadata['wiki']['published']),
  }
