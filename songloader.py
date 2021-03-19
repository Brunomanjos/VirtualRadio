import os

import numpy as np
import soundfile
from pydub import AudioSegment


def as_formats(path):
    segment = AudioSegment.from_file(path)
    audio = np.frombuffer(segment.raw_data, dtype='int16').reshape(-1, segment.channels)
    return audio, segment.frame_rate


def sf_formats(path):
    return soundfile.read(path, dtype='int16')


def load_song(path):
    ext = os.path.splitext(path)[1].lower()

    try:
        return loaders[ext](path)
    except KeyError:
        raise IOError(f'Unrecognized file type: {ext}') from None


loaders = {
    '.mp3': as_formats,
    '.flv': as_formats,
    '.ogg': as_formats,
    '.wav': as_formats,
    '.raw': as_formats
}
loaders.update({f'.{key.lower()}': sf_formats for key in soundfile.available_formats().keys()})

extensions = list(loaders.keys())
