from uuid import UUID

from . import Story
from .utils import Decryption, ByteBuffer

class Device:
    def __init__(self, path):
        self.mountpoint = path
        self.devkey = None
        self.devicekey = None
        self.story_list, stories = [], []

        # external flash hardcoded value
        # 91BD7A0A A75440A9 BBD49D6C E0DCC0E3
        self.raw_key_generic = [0x91BD7A0A, 0xA75440A9, 0xBBD49D6C, 0xE0DCC0E3]
        self.lunii_generic_key = self.__vectkey_to_bytes(self.raw_key_generic)

        self.__get_hw_info()
        self.__get_stories()

    def populate(self):
        self.__get_stories()

    def parse_stories(self):
        self.__parse_stories()

    def parse_story(self, uuid):
        if uuid in self.story_list:
            return Story(self.mountpoint, uuid, (self.device_key, self.lunii_generic_key))
        return None
        
    def __get_hw_info(self):
        md_path = f"{self.mountpoint}/.md"

        with open(md_path, 'rb') as fp_md:
            fp_md.seek(fp_md.tell() + 6)

            self.fw_vers_major = int.from_bytes(fp_md.read(2), 'little')
            self.fw_vers_minor = int.from_bytes(fp_md.read(2), 'little')
            self.snu = int.from_bytes(fp_md.read(8), 'little')
            
            fp_md.seek(0x100)
            self.raw_devkey = fp_md.read(0x100)

            # I'll rewrite that with utils.py:ByteBuffer

            decryptionClient = Decryption(self.lunii_generic_key, bytes=self.raw_devkey)
            dec = decryptionClient.decrypted

            # Reordering Key components
            self.device_key = dec[8:16] + dec[0:8]

    def __vectkey_to_bytes(self, key_vect):
        joined = [k.to_bytes(4, 'little') for k in key_vect]
        return b''.join(joined)
    
    def __get_stories(self):
        self.story_list = []
        with open(self.mountpoint + '/.pi', 'rb') as fp_pi:
            loop_again = True
            while loop_again:
                next_uuid = fp_pi.read(16)
                if next_uuid:
                    self.story_list.append(UUID(bytes=next_uuid))
                else:
                    loop_again = False

    def __parse_stories(self):
        self.stories = []
        for story in self.story_list:
            self.stories.append(Story(self.mountpoint, story, (self.device_key, self.lunii_generic_key)))
      