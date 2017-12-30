# Copyright 2017 Itamar Ostricher

"""Utils for Make My Music Metadata Great Again."""

import os
from os.path import join
import re

from colorama import Fore


_TOKEN_MAP = {
    'a': 'a',
    'and': 'and',
    'for': 'For',
    'from': 'From',
    'in': 'In',
    'is': 'Is',
    'it': 'It',
    'of': 'of',
    'on': 'On',
    'to': 'to',
    'the': 'the',
}

_BAD_FILENAME_CHARS = {
    '/': '_',
    '\\': '_',
    ':': '-',
}

_MUSIC_FILE_EXTENSIONS = frozenset(
    {'.mp3', '.flac', '.aac', '.wav', '.ogg', '.oga', '.wma'})


def norm_fname(fname):
  """Return normalized track name that can be used as a filename."""
  for bad_char, good_char in _BAD_FILENAME_CHARS.items():
    fname = fname.replace(bad_char, good_char)
  return fname


def norm_token(token, prev_token):
  """Return normalized token from a track / album title."""
  # FIXME: smarter context-aware normalization
  # (e.g. words with "touching" markup (`(the..)`),
  #  words following markup (`Foo: the`), ...
  token = _TOKEN_MAP.get(token.lower(), token)
  if prev_token in (None, '-', '_'):
    return token.capitalize()
  return token


def norm_title(title):
  """Return normalized track / album title."""
  norm_tokens = []
  prev_token = None
  for token in title.split(' '):
    norm_tokens.append(norm_token(token, prev_token))
    prev_token = token
  return ' '.join(norm_tokens)


def gen_albums(base_dir, ignore):
  """Generate albums under `base_dir`,
     as tuples of (album_path, artist, album, album_year).

  Assumed dir structure:
  - Top-level `base_dir` contains a directory per artist, with artist name.
  - Every artist dir contains a directory per album,
    using the naming convention: "[4-digit-album-year] Album-Name"

  Skip albums / artists in the ignore lists.
  Skip directories that don't match the expected naming convention.
  Skip directories that begin with ".".
  """
  for artist in os.listdir(base_dir):
    if artist.startswith('.') or artist in ignore['artists']:
      print(f'{Fore.YELLOW}Skipping ignored artist dir {artist}')
      continue
    artist_dir = join(base_dir, artist)
    for album_dirname in os.listdir(artist_dir):
      m = re.match(R'\[(\d{4})\] (.*)', album_dirname)
      if m is None:
        print(f'{Fore.YELLOW}Skipping unmatched dir: {artist}/{album_dirname}')
        continue
      album, album_year = m.group(2), m.group(1)
      if album in ignore['albums']:
        print(f'{Fore.YELLOW}Skipping ignored album dir {album}')
        continue
      album_path = join(artist_dir, album_dirname)
      yield album_path, artist, album, album_year


def get_album_files(album_path):
  """Return all files and sub-directories under `album_path`,
     divided into music_files, other_files, and sub_dirs.
  """
  prefix_len = len(album_path) + 1
  sub_dirs, music_files, other_files = [], [], []

  def is_music_file(file_name):
    return os.path.splitext(file_name)[-1].lower() in _MUSIC_FILE_EXTENSIONS

  for root, dirs, file_names in os.walk(album_path):
    sub_dirs.extend(join(root, dir_name)[prefix_len:] for dir_name in dirs)
    music_files.extend(join(root, fname)[prefix_len:]
                       for fname in file_names if is_music_file(fname))
    other_files.extend(join(root, fname)[prefix_len:]
                       for fname in file_names if not is_music_file(fname))
  return music_files, other_files, sub_dirs
