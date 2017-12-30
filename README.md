# Make My Music Metadata Great Again

Script for fixing up the filenames in my music library

**Warning: This is not a general purpose tool. It was built for my specific use-case.**

## Install

This tool runs directly from source code, and requires Python 3.6+ and [Pipenv](https://docs.pipenv.org/).

```sh
git clone git@github.com:itamaro/make-my-music-metadata-great-again.git
cd make-my-music-metadata-great-again
pipenv install
```

You'll also need a [LastFM API key](https://www.last.fm/api), as this script uses the LastFM API to retrieve music album metadata.

The script expects to find the API key in an environment variable named `API_KEY`.
The recommended way to provide it when working with Pipenv is with a `.env` file:

```sh
echo 'API_KEY="your-api-key"' > .env
```

Please don't publish your API key :-)

## Run On Music Library

Simply run the following command from the cloned script directory:

```sh
pipenv run python -m mmmmga --dir /path/to/music/dir
```

The detailed help:

```sh
pipenv run python -m mmmmga --help
Make My Music Metadata Great Again.

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
```

## Notes

The script expects `dir` to have a specific structure -
first level should contain one directory per artist, named the same as the artist,
and the second level should contain one directory per album, with the name following the convention `[4-digit-release-year] Album Name`.

Example:

```
/my/music/library
├── "Adagio"
│   └── "[2003] Underworld"
├── "Dissonant"
│   └── "[2005] Consolidated Reality Fragments"
├── "Emerson, Lake & Palmer"
│   └── "[1972] Pictures at an Exhibition"
├── "Faith No More"
│   └── "[1989] The Real Thing"
├── "King Crimson"
│   └── "[1974] Red"
├── "Muse"
│   └── "[2001] Origin of Symmetry"
├── "Opeth"
│   ├── "[1996] Morningrise"
│   └── "[1998] My Arms Your Hearse"
├── "Orphaned Land"
│   └── "[2004] The Calm Before the Flood"
├── "Pain of Salvation"
│   └── "[2005] Be_ Original Stage Production"
├── "Red Hot Chili Peppers"
│   └── "[1991] Blood Sugar Sex Magik"
└── "Rush"
    ├── "[1976] 2112"
    ├── "[1981] Moving Pictures"
    └── "[2003] Rush In Rio"
```

## Known Limitations

The script is best-effort, in terms of finding a matching album.
It uses the artist name and album name from the filesystem, and assumes that whatever it gets back (if any) is correct.
This assumption often doesn't hold with albums that has many editions, special releases, or weird characters in their names.

When downloading album art from LastFM, the script saves them as JPG's without respecting the remote format (although it's usually PNG...).

The script attempts to match existing music files with album tracks using "string similarity ratio" (see [Python's SequenceMatcher for more details](https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher.ratio)) in the order of the album tracks. This might have an undesired side effect, where an "early" track matches a file that's actually a later track, making everything that follows messed up (there's no two-sided optimization for matches).

The script attempts to detect multi-disc releases from the LastFM API by detecting discontinuities in the track numbers, which is not always reliable.

YMMV...
