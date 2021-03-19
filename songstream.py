from threading import Thread, Condition

import numpy as np
import sounddevice

CHUNK_SIZE = 1024


class SongStream:

    def __init__(self, song_data, frame_rate, volume=1.0):
        self._song_data = song_data
        self._frame_rate = frame_rate
        self._volume = volume
        self._chunk_index = 0
        self._playing = False
        self._condition = Condition()

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = min(1, max(0, value))

    @property
    def seconds(self):
        return self._chunk_index / self._frame_rate

    @property
    def length(self):
        return self._song_data.shape[0] / self._frame_rate

    @property
    def playing(self):
        return self._playing

    def set_position(self, pos):
        self._chunk_index = int(max(0, pos) * self._frame_rate)

    def play(self, block=True):
        if not block:
            Thread(target=self.play, daemon=True).start()
            return

        with self._condition:
            if self._playing:
                return

            self._playing = True

        frames, channels = self._song_data.shape

        stream = sounddevice.OutputStream(self._frame_rate, channels=channels, dtype=np.int16)
        stream.start()

        while self._chunk_index < frames:
            if not self._playing:
                return

            chunk = self._song_data[self._chunk_index:self._chunk_index + CHUNK_SIZE]
            self._chunk_index += CHUNK_SIZE

            if self.volume != 1:
                chunk = (chunk * self.volume).astype(np.int16)

            stream.write(chunk)

        self._chunk_index = 0
        self._playing = False

    def stop(self):
        self._playing = False
        self._chunk_index = 0

    def pause(self):
        self._playing = False
