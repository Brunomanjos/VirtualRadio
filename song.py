from threading import Lock

import numpy as np
import sounddevice

import songloader

CHUNK_SIZE = 1024

playing_song = None
player_lock = Lock()


class Song:

    def __init__(self, song_path, load=False):
        self._path = song_path
        self._info = songloader.info(song_path, False)
        self._image = None

        self._song_data = None
        self._frame_rate = None
        self._volume = 1
        self._chunk_index = 0
        self._playing = False

        if load:
            self.load()

    def load(self):
        if self._frame_rate is not None and self._song_data is not None:
            return

        self._song_data, self._frame_rate = songloader.load(self._path)
        self._chunk_index = 0
        self._info.duration = self._song_data.shape[0] / self._frame_rate  # slightly more precise duration

    def unload(self):
        self._frame_rate = None
        self._song_data = None

    def play(self):
        global playing_song

        with player_lock:
            if playing_song:
                playing_song.stop()

            playing_song = self

        self.load()
        self._playing = True

        frames, channels = self._song_data.shape

        stream = sounddevice.OutputStream(self._frame_rate, channels=channels, dtype=np.int16)
        stream.start()

        while self._chunk_index < frames:
            if not self._playing:
                break

            chunk = self._song_data[self._chunk_index:self._chunk_index + CHUNK_SIZE]
            self._chunk_index += CHUNK_SIZE

            if self.volume != 1:
                chunk = (chunk * self.volume).astype(np.int16)

            stream.write(chunk)

        self._chunk_index = 0
        self._playing = False
        stream.close()

    def stop(self):
        self._playing = False

    def pause(self):
        self._playing = False

    @property
    def path(self):
        return self._path

    @property
    def info(self):
        return self._info

    @property
    def image(self):
        if not self._image:
            self._image = songloader.info(self._path, True).get_image()

        return self._image

    @property
    def title(self):
        return self._info.title

    @property
    def duration(self):
        return self._info.duration

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = min(1, max(0, value))

    @property
    def position(self):
        if self._frame_rate is None:
            return 0
        return self._chunk_index / self._frame_rate

    @position.setter
    def position(self, seconds):
        if self._frame_rate is not None:
            self._chunk_index = int(max(0, seconds) * self._frame_rate)

    @property
    def playing(self):
        return self._playing

    @playing.setter
    def playing(self, value):
        self._playing = value
