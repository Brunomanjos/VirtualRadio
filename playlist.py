import json
import os
import random
from dataclasses import dataclass, fields, field

from song import Song
from songloader import extensions


@dataclass
class PlaylistData:
    _songs: dict[str, int] = field(default_factory=dict)
    _paths: list[str] = field(default_factory=list)

    @staticmethod
    def get(playlist):
        data = {}
        for field in fields(PlaylistData):
            data[field.name] = getattr(playlist, field.name)
        return data

    @staticmethod
    def set(playlist, data):
        for field in fields(PlaylistData):
            setattr(playlist, field.name, data[field.name])


class Playlist:

    def __init__(self, song_paths):
        if isinstance(song_paths, str):
            self._paths = [song_paths]
        else:
            self._paths = song_paths

        self._songs = {}
        self._song = None

    def next(self, load=False):
        next_song = None

        while next_song is None:
            self._reload_songs()
            chosen_song = self._choose_song()

            try:
                next_song = Song(chosen_song, load)
            except IOError:
                continue  # file is corrupted or was removed on race condition

            self._update_weights(chosen_song)

        self._song = next_song
        return next_song

    def get(self):
        return self._song

    def save(self, output_path):
        with open(output_path, 'w') as file:
            json.dump(PlaylistData.get(self), file)

    @staticmethod
    def load(path):
        with open(path, 'r') as file:
            data = json.load(file)
            playlist = Playlist([])
            PlaylistData.set(playlist, data)
            return playlist

    def add_path(self, path):
        if isinstance(path, str):
            self._paths.append(path)
        else:
            self._paths.extend(path)

    def remove_path(self, path):
        if isinstance(path, str):
            self._paths.remove(path)
        else:
            for directory in path:
                self._paths.remove(directory)

    def _reload_songs(self):
        def get_songs(path):
            for root, _, songs in os.walk(path):
                for song in songs:
                    if os.path.splitext(song)[1] in extensions:
                        yield os.path.join(root, song)

        updated_songs = {}
        for root in self._paths:
            for song in get_songs(root):
                updated_songs[song] = self._songs.get(song, 1)

        self._songs = updated_songs

    def _choose_song(self):
        songs = list(self._songs.keys())
        weights = list(self._songs.values())
        return random.choices(songs, weights, k=1)[0]

    def _update_weights(self, chosen_song):
        for song in self._songs:
            self._songs[song] += 1

        self._songs[chosen_song] = 0

    @property
    def paths(self):
        return self._paths.copy()
