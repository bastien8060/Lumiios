import io
import os
import json
import time
import struct
import requests
from typing import Dict, List, Optional, Union, Tuple

import vlc
import xxtea
import climage
from PIL import Image
from appdirs import AppDirs

from pkg_resources import resource_stream

class Decryption:
    def __lunii_tea_rounds(self, buffer):
        return int(1 + 52 / (len(buffer)/4))
    
    def __init__(self, key, padding=None, rounds=None, path=None, bytes=None):
        self.key = key
        self.padding = padding
        self.rounds = rounds
        self.decrypted = None
        self.decrypted_buffer = None

        
        #check if path or bytes is set
        if path is None:
            self.decrypted = xxtea.decrypt(bytes, self.key, padding=False, rounds=self.__lunii_tea_rounds(bytes))
            return

        else:
            fp = open(path, 'rb')

            # processing first block
            ciphered = fp.read(0x200)
            if len(ciphered) == 0:
                return
            
            self.decrypted = xxtea.decrypt(ciphered, self.key, padding=False, rounds=self.__lunii_tea_rounds(ciphered))

            # check if left over bytes, that are already decrypted
            left = fp.read()
            if len(left) != 0:
                self.decrypted += left

            fp.close()

            self.decrypted_buffer = io.BytesIO(self.decrypted)

            return

class ByteBuffer:
    def __init__(self, data, byte_order='!'):
        self.data = data
        self.offset = 0
        self.byte_order = byte_order

    def get(self):
        if self.offset + 1 > len(self.data):
            raise ValueError("Not enough bytes remaining in buffer")
        b = self.data[self.offset]
        self.offset += 1
        return b

    def get_short(self):
        if self.offset + 2 > len(self.data):
            raise ValueError("Not enough bytes remaining in buffer")
        s = struct.unpack_from(self.byte_order + "h", self.data, self.offset)[0]
        self.offset += 2
        return s

    def get_int(self):
        if self.offset + 4 > len(self.data):
            raise ValueError("Not enough bytes remaining in buffer")
        i = struct.unpack_from(self.byte_order + "i", self.data, self.offset)[0]
        self.offset += 4
        return i
    
    def read_n_bytes(self, n):
        if self.offset + n > len(self.data):
            raise ValueError("Not enough bytes remaining in buffer")
        b = self.data[self.offset:self.offset + n]
        self.offset += n
        return b

    def seek(self, offset, whence=0):
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = len(self.data) + offset
        else:
            raise ValueError("Invalid whence argument")
        if self.offset < 0 or self.offset > len(self.data):
            raise ValueError("Invalid offset argument")

class ImageAsset:
    """
    BPM Images
    Format                                   : RLE4
    Width                                    : 320 pixels
    Height                                   : 240 pixels
    Color space                              : RGB
    Bit depth                                : 4 bits
    """
    def __init__(self, image_type: str, path: str, key: str):
        self.image_type = image_type
        self.path = path

        self.content = Decryption(key, path=path).decrypted
    
    def show(self):
        img = Image.open(io.BytesIO(self.content))
        img.save('/tmp/image.png')

        # display the image
        img = Image.open('/tmp/image.png')
    
        output = climage.convert('/tmp/image.png', 'ansi', width=40)

        print(output)
        
    def __repr__(self):
        return f"ImageAsset({self.image_type}, {self.path})"

    def __str__(self):
        return f"ImageAsset({self.image_type}, {self.path})"

class AudioAsset:
    """
    Audio
    Format                                   : MPEG Audio
    Format version                           : Version 1
    Format profile                           : Layer 3
    Duration                                 : 1 s 881 ms
    Bit rate mode                            : Variable
    Bit rate                                 : 61.8 kb/s
    Minimum bit rate                         : 32.0 kb/s
    Channel(s)                               : 1 channel
    Sampling rate                            : 44.1 kHz
    Frame rate                               : 38.281 FPS (1152 SPF)
    Compression mode                         : Lossy
    Stream size                              : 14.2 KiB (97%)
    Writing library                          : LAME3.100
    Encoding settings                        : -m m -V 4 -q 0 -lowpass 17.5 --vbr-new -b 32
    """
    def __init__(self, audio_type: str, path: str):
        self.audio_type = audio_type
        self.path = path
        
        with open(path, 'rb') as f:
            self.content = f.read()

    @property
    def is_playing(self):
        return self.player.get_state() != vlc.State.Ended

    def play(self):
        # create a VLC instance
        self.instance = vlc.Instance('--no-xlib')

        # create a new media object
        self.media = self.instance.media_new(self.path)

        # create a new media player
        self.player = self.instance.media_player_new()

        # set the media player as the media
        self.player.set_media(self.media)

        time.sleep(0.25)

        # play the media
        self.player.play()

    def release(self):
        #release the player
        self.player.release()
        self.instance.release()
        

    def __repr__(self):
        return f"AudioAsset({self.audio_type}, {self.path})"

    def __str__(self):
        return f"AudioAsset({self.audio_type}, {self.path})"
        


class Transition:
    def __init__(self, to_index: int):
        self.to_index = to_index

class ControlSettings:
    def __init__(self, dict_controls):
        self.wheel = dict_controls.get('wheel', False)
        self.ok = dict_controls.get('ok', False)
        self.home = dict_controls.get('home', False)
        self.pause = dict_controls.get('pause', False)
        self.autoplay = dict_controls.get('autoplay', False)

class StageNode:
    def __init__(self,
                 index: int,
                 assets: Tuple[ImageAsset, AudioAsset] = None,
                 next_transitions: List[Transition] = None,
                 home_transitions: List[Transition] = None,
                 control_settings: ControlSettings = None
                 ):
        self.index = index
        self.assets = assets
        self.next_transitions = next_transitions
        self.home_transitions = home_transitions
        self.control_settings = control_settings

class ActionNode:
    def __init__(self, options, metadata):
        self.options = options
        self.metadata = {
            'choice_index': metadata['choice_index'],
            'choice_count': metadata['choice_count'],
        }

class StoryMetadata:
    def __init__(self, filename=None, refresh=False):
        self.filename = filename
        if refresh:
            self.__fetch_metadata()
        self.metadata = self.load_titles()

    def __fetch_metadata(self, url: str, lang: str = "fr_FR") -> None:
        response = requests.get(url).json()

        results = []

        for key in response["response"]:
            entry = response["response"][key]
            localized_infos = entry.get("localized_infos", {}).get(lang, {})
            if not localized_infos:
                continue
            else:
                title = localized_infos.get("title", "")
            result = {
                "uuid": entry.get("uuid", ""),
                "title": title,
                "keywords": entry.get("keywords", ""),
                "subtitle": entry.get("subtitle", ""),
            }
            results.append(result)

        self.filename = self.filename or os.path.join(
            AppDirs("lunii", "lunii").user_data_dir, "titles.json"
        )
        with open(self.filename, 'w') as f:
            json.dump(results, f, indent=4)

    def load_titles(self):
        self.filename = self.filename or os.path.join(
            AppDirs("lunii", "lunii").user_data_dir, "titles.json"
        )
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return json.load(resource_stream('lunii', 'data/titles.json'))

    def get_metadata(self, uuid):
        for story in self.metadata:
            if str(uuid).lower() in story['uuid'].lower():
                return story
        return {}
