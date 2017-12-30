# Copyright 2017 Itamar Ostricher

"""Make My Music Metadata Great Again.

Usage:
  mmmmga.py [--dir <dir>] [--no-delete] [--force]
  mmmmga.py (-h | --help)
  mmmmga.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --dir <dir>   Start scanning from this directory [default: .].
  --no-delete   If specified, will avoid deletions.
  --force       If specified, will also process already finished albums.
"""

from difflib import SequenceMatcher
import json
import os
from os.path import join
import shelve
import shutil

from colorama import Fore, Style
import requests

from .musicapi import get_album_metadata
from .utils import gen_albums, get_album_files, norm_fname, norm_title


def match_music_files(files, metadata):
  """Return list of matches from existing files to metadata-based files."""
  multi_disc = len(metadata['discs']) > 1
  moves = []
  for disc_num, disc_tracks in enumerate(metadata['discs']):
    for track in disc_tracks:
      if len(files) == 0:
        break
      # desired track filename from the metadata:
      track_fname = ((f'[CD{disc_num+1}] ' if multi_disc else '') +
                     f'{track["pos"]:02} {norm_fname(track["name"])}')

      def sort_func(existing_name):
        return SequenceMatcher(None, existing_name, track_fname).ratio()

      # find existing file that best matches the desired track filename,
      # using SequenceMatcher ratio
      existing_name = sorted(files, key=sort_func, reverse=True)[0]
      track_fname += os.path.splitext(existing_name)[-1]
      moves.append({'src': existing_name, 'dst': track_fname})
      files.remove(existing_name)
  return moves


def match_album_art_files(files, metadata):
  """Return list of matches from existing files to album art files +
     list of album art files to download.
  """
  moves = []
  need_small_img, need_large_img = True, True
  lower_case_file_names = [os.path.basename(x.lower()) for x in files]
  alt_folder_img = f'{metadata["artist"]} - {metadata["album"]}.jpg'.lower()
  if 'folder.jpg' in lower_case_file_names:
    need_large_img = False
    other_file = files[lower_case_file_names.index('folder.jpg')]
    moves.append({'src': other_file, 'dst': 'Folder.jpg'})
    lower_case_file_names.remove('folder.jpg')
    files.remove(other_file)
  elif alt_folder_img in lower_case_file_names:
    need_large_img = False
    other_file = files[lower_case_file_names.index(alt_folder_img)]
    moves.append({'src': other_file, 'dst': 'Folder.jpg'})
    lower_case_file_names.remove(alt_folder_img)
    files.remove(other_file)
  if 'albumartsmall.jpg' in lower_case_file_names:
    need_small_img = False
    other_file = files[lower_case_file_names.index('albumartsmall.jpg')]
    moves.append({'src': other_file, 'dst': 'AlbumArtSmall.jpg'})
    lower_case_file_names.remove('albumartsmall.jpg')
    files.remove(other_file)
  downloads = []
  # FIXME: apply correct image extension - don't assume jpg
  if need_small_img and metadata['images'].get('small'):
    downloads.append({'src': metadata['images']['small'],
                      'dst': 'AlbumArtSmall.jpg'})
  if need_large_img and metadata['images'].get('large'):
    downloads.append({'src': metadata['images']['large'],
                      'dst': 'Folder.jpg'})
  return moves, downloads


def prompt_user(metadata, keeps, moves, deletes, downloads):
  """Print out a summary of planned operations, prompt user for confirmation,
     and return the prompt result (unless there are no operations).
  """
  done = True
  if keeps:
    print(f'{Style.BRIGHT}== Going to keep {len(keeps)} files as they are:')
    for op in keeps:
      print(f'{Fore.GREEN}   {op}')
    print()
  if moves:
    done = False
    print(f'{Style.BRIGHT}== Going to move {len(moves)} files:')
    moves_width = max(len(op['src']) for op in moves) + 2
    for op in moves:
      print(f'   {Fore.YELLOW}{op["src"].ljust(moves_width)} '
            f'{Fore.WHITE}==>  {Fore.GREEN}{op["dst"]}')
    print()
  if deletes:
    done = False
    print(f'{Style.BRIGHT}== Going to delete {len(deletes)} files & dirs:')
    for op in deletes:
      print(f'{Fore.RED}   {op}')
    print()
  if downloads:
    done = False
    print(f'{Style.BRIGHT}== Going to download {len(downloads)} files:')
    src_width = max(len(op['src']) for op in downloads) + 2
    for op in downloads:
      print(f'{Fore.GREEN}   {op["src"].ljust(src_width)} '
            f'{Fore.WHITE}==>  {Fore.GREEN}{op["dst"]}')
    print()
  # Looks like the wiki.published date is not reliable...
  # norm_album_dir = f'[{metadata["published"].year}] {metadata["album"]}'
  # cur_album_dir = os.path.basename(album_path)
  # if norm_album_dir != cur_album_dir:
  #   done = False
  #   print(Style.BRIGHT + '== Going to rename album dir:')
  #   print(f'   {Fore.YELLOW}{cur_album_dir}  {Fore.WHITE}==>  '
  #         f'{Fore.GREEN}{norm_album_dir}\n')

  if done:
    print(f'{metadata["artist"]} - {metadata["album"]} all good\n')
    return 'Finished'
  answer = input('OK to continue? [yN] ')
  if answer.lower() not in ('y', 'yes'):
    return 'Cancel'
  return 'Proceed'


def fix_album_dir(album_path, metadata, no_delete=False):
  """Fix the metadata of album at `album_path` with `metadata`."""
  music_files, other_files, sub_dirs = get_album_files(album_path)
  moves, downloads = match_album_art_files(other_files, metadata)
  moves.extend(match_music_files(music_files, metadata))

  deletes = []
  if not no_delete:
    deletes = music_files + other_files + sub_dirs
  keeps = [op['src'] for op in moves if op['src'] == op['dst']]
  moves = [op for op in moves if op['src'] != op['dst']]

  prompt = prompt_user(metadata, keeps, moves, deletes, downloads)
  if prompt == 'Finished':
    return True
  if prompt == 'Cancel':
    return False

  for op in moves:
    shutil.move(join(album_path, op['src']), join(album_path, op['dst']))
  for op in deletes:
    if os.path.isfile(op):
      os.remove(join(album_path, op))
    elif os.path.isdir(op):
      shutil.rmtree(op)
    else:
      print(f'{Fore.RED}Not sure how to delete {op} - skipping')
  for op in downloads:
    stream = requests.get(op['src'], stream=True)
    stream.raw.decode_content = True
    with open(join(album_path, op['dst']), 'wb') as out_file:
      shutil.copyfileobj(stream.raw, out_file)
    del stream
  print(f'Finished fixing up {metadata["artist"]} - {metadata["album"]}\n')

  return True


def get_ignores():
  """Load and return the ignore lists from file."""
  try:
    with open('ignorelist', 'r') as ignore_file:
      ignore = json.load(ignore_file)
      # turn into sets
      ignore['artists'] = set(ignore.get('artists', []))
      ignore['albums'] = set(ignore.get('albums', []))
  except FileNotFoundError:
    ignore = {'artists': {}, 'albums': {}}
  return ignore


def run(base_dir, no_delete=False, force=False):
  """Iterate over albums under `base_dir`, and fix their metadata."""
  ignore = get_ignores()
  with shelve.open('.status') as status:
    for album_path, artist, album, album_year in gen_albums(base_dir, ignore):
      album_key = f'{artist} - [{album_year}] - {album}'
      if not force and status.get(album_key) == 'Finished':
        print(f'Skipping already finished album {album_key}')
        continue
      print(f'\n\n{Style.BRIGHT}= Working on {album_key} =\n')
      try:
        album_metadata = get_album_metadata(artist, album)
        status[album_key] = (
            'Finished' if fix_album_dir(album_path, album_metadata, no_delete)
            else 'Skipped')
      except Exception as ex:
        print(f'{Fore.RED}Failed fixing up {album_key}: {ex}')
        status[album_key] = 'Error'
