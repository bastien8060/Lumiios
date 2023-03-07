import os

from .utils import Decryption, ByteBuffer
from .utils import ImageAsset, AudioAsset
from .utils import ActionNode, StageNode, ControlSettings, Transition
from .utils import StoryMetadata

class Story:
    def __init__(self, path, uuid, keys:tuple):
        self.mountpoint = path

        self.full_uuid = uuid
        self.uuid = uuid.hex[-8:].upper()

        self.__device_key = keys[0]
        self.__lunii_generic_key = keys[1]

        self.version, self.night_mode, self.authorized = None, False, False
        self.__si, self.__ri, self.__li = None, None, None     

        self.__ri_path = self.__get_local_filepath('ri')
        self.__si_path = self.__get_local_filepath('si')
        self.__li_path = self.__get_local_filepath('li')
        self.__bt_path = self.__get_local_filepath('bt')
        self.__ni_path = self.__get_local_filepath('ni')
        self.__nm_path = self.__get_local_filepath('nm')

        self.__rf_path = self.__get_local_filepath('rf/')
        self.__sf_path = self.__get_local_filepath('sf/')

        self.nodes_index_list = []
        self.stage_nodes = {}

        self.cover_audio = None

        self.populate()

    def populate(self):
        self.__verify_auth()
        self.__get_story_metadata()
        self.__get_story_title()
        self.__get_songs_index()
        self.__get_resources_index()

        self.__get_list_node_index()
        self.__get_action_node_index()

        self.__get_cover_audio()

    def __get_cover_audio(self):
        # reference to AudioAsset of node #0
        self.cover_audio = self.stage_nodes.get(0,{}).assets.get('audio', None)

    def __get_story_metadata(self):
        with open(self.__ni_path, 'rb') as fp_ni:
            ni = fp_ni.read(512)
            buffer = ByteBuffer(ni, '<')
            s1 = buffer.get_short()  # read the first short integer
            s2 = buffer.get_short()  # read the second short integer
            self.version = s2

        # night mode is enabled if the file exists
        self.night_mode = os.path.exists(self.__nm_path)

    def __get_story_title(self):
        storyMetadataClient = StoryMetadata("./misc/titles.json")
        self.title = storyMetadataClient.get_metadata(self.full_uuid).get('title', 'Unknown Story')

    def __get_local_filepath(self, file):
        return self.mountpoint + '/.content/' + self.uuid + '/' + file

    def __get_songs_index(self):
        # Song Index
        # The file is organized as a list of 12 Bytes strings
        # first decrypt the file with generic key
        with Decryption(self.__lunii_generic_key, path=self.__si_path).decrypted_buffer as fp_si:
            loop_again = True
            str_list = []
            while loop_again:
                char_array = fp_si.read(12)
                if char_array:
                    str_list.append(char_array.decode('utf-8'))
                else:
                    loop_again = False
            self.__si = str_list

    def __get_resources_index(self):
        # Resource Index
        # The file is organized as a list of 12 Bytes strings
        # first decrypt the file with generic key
        with Decryption(self.__lunii_generic_key, path=self.__ri_path).decrypted_buffer as fp_ri:
            loop_again = True
            str_list = []
            while loop_again:
                char_array = fp_ri.read(12)
                if char_array:
                    str_list.append(char_array.decode('utf-8'))
                else:
                    loop_again = False
            self.__ri = str_list

    def __get_abs_node_idx(self, node_idx):
        if node_idx < 0:
            return -1
        else:
            return self.nodes_index_list[node_idx]
    

    def __get_list_node_index(self):
        # List Node Index
        # The file is organized as an array of 4 bytes integers
        # first decrypt the file with generic key
        fp_li = Decryption(self.__lunii_generic_key, path=self.__li_path).decrypted_buffer
        bb = ByteBuffer(fp_li.read(), '<')

        #count = fp_li_size_bytes / 4
        count = int(os.path.getsize(self.__li_path) / 4)
        
        self.nodes_index_list = []
        for i in range(count):
            self.nodes_index_list.append(bb.get_int())   


    def __get_action_node_index(self):
        self.stage_nodes = {}
        action_nodes_options_count = {}
        transitions_with_action = {}

        # use ByteBuffer to read the file
        # open ni as rb
        
        fp_ni = open(self.__ni_path, 'rb')

        bb = ByteBuffer(fp_ni.read(), '<')
        
        # Nodes index file format version (1)
        bb.get_short()

        # Story pack version
        version = bb.get_short()
        # Start of actual nodes list in this file (0x200 / 512)

        nodes_list = bb.get_int()
        # Size of a stage node in this file (0x2C / 44)

        node_size = bb.get_int()
        # Number of stage nodes in this file

        stage_nodes_count = bb.get_int()
        # Number of images (in RI file and rf/ folder)

        image_assets_count = bb.get_int()
        # Number of sounds (in SI file and sf/ folder)

        sound_assets_count = bb.get_int()
        # Is factory pack (boolean) set to true to avoid pack inspection by official Luniistore application

        factory_disabled = bb.get() != 0x00

        for i in range(stage_nodes_count):
            fp_ni.seek(0x200 + (i * node_size))
            bb = ByteBuffer(fp_ni.read(node_size), '<')

            ri_index = bb.get_int() # index in ri file
            si_index = bb.get_int() # index in si file

            next_node_index = bb.get_int() # index loaded from li for next in ni
            next_nodes_count = bb.get_int() # how many choices for next_node?
            # Choices Range = next_node_index -> next_node_index + next_nodes_count
            next_node_selected = bb.get_int() # huh... always 0 for some reason?

            home_node_index = bb.get_int()
            home_nodes_count = bb.get_int()
            home_node_selected = bb.get_int() # to ignore too

            controls = {
                'wheel': bb.get_short() != 0,
                'ok': bb.get_short() != 0,
                'home': bb.get_short() != 0,
                'pause': bb.get_short() != 0,
                'autoplay': bb.get_short() != 0
            }

            next_transitions = []
            if next_node_index != -1 and next_nodes_count != -1 and next_node_selected != -1:
                for count in range(next_nodes_count):
                    next_transitions.append(Transition(self.__get_abs_node_idx(next_node_index) + count))

            home_transitions = []
            if home_node_index != -1 and home_nodes_count != -1 and home_node_selected != -1:
                for count in range(home_nodes_count):
                    home_transitions.append(Transition(self.__get_abs_node_idx(home_node_index) + count))

            assets = {
                'image': None,
                'audio': None
            }

            if ri_index != -1:
                image_path = self.__rf_path + self.__ri[ri_index].replace("\\", "/")
                key = self.__lunii_generic_key
                assets['image'] = ImageAsset('image/bmp', image_path, key)

            audio = None
            if si_index != -1:
                audio_path = self.__sf_path + self.__si[si_index].replace("\\", "/")
                assets['audio'] = AudioAsset('audio/mpeg', audio_path)

            stage_node = StageNode(
                i,
                assets,
                next_transitions,
                home_transitions,
                ControlSettings(controls),
            )
            self.stage_nodes[i] = stage_node

        li_fp = Decryption(self.__lunii_generic_key, path=self.__li_path).decrypted_buffer
        li_bb = ByteBuffer(li_fp.read(), '<')

       


    def __verify_auth(self):
        # bt file is encrypted with the device key
        # It is made by ciphering the 0x40 first bytes for .ri file with device specific key.

        try:
            with open(self.__bt_path, 'rb') as fp_bt:
                bt = fp_bt.read()

            with open(self.__ri_path, 'rb') as fp_ri:
                ri = fp_ri.read(0x40)

            decryptionClient = Decryption(self.__device_key, bytes=bt)
            dec = decryptionClient.decrypted

            if dec == ri:
                self.authorized = True
            else:
                self.authorized = False
        except:
            self.authorized = False

