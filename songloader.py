import os
import wave

import numpy as np
from pydub import AudioSegment
from tinytag.tinytag import TinyTag


def info(path, image=False):
    return TinyTag.get(path, image=image)


def load(path):
    ext = os.path.splitext(path)[1].lower()

    try:
        return _loader[ext](path)
    except KeyError:
        raise IOError(f'Unrecognized file type: {ext}') from None


def mp3_loader(path):
    segment = AudioSegment.from_file(path)
    audio = np.frombuffer(segment.raw_data, dtype='int16').reshape(-1, segment.channels)
    return audio, segment.frame_rate


def wav_loader(path):
    with wave.open(path, 'r') as file:
        audio = np.frombuffer(file.readframes(-1), dtype='int16').reshape(-1, file.getnchannels())
        return audio, file.getframerate()


_loader = {
    '.mp3': mp3_loader,
    '.wav': wav_loader
}

extensions = list(_loader.keys())
