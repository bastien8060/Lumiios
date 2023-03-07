import time
from typing import List

class StoryPlayer:
    def __init__(self, story, interactive=True, display_cb=None, audio_cb=None):
        self.story = story
        self.current_node_idx = 0
        self.audio_supressed = False
        self.playing = True
        self.node_history = [0]

        self.interactive = interactive
        self.display_cb = display_cb
        self.audio_cb = audio_cb
        self.pending_input = None
    
    def walk_to_node(self, node_index):
        self.current_node_idx = node_index
        self.node_history.append(self.current_node_idx)

    def reset_to_node(self, node_index):
        self.current_node_idx = node_index
        self.node_history = [node_index]

    def walk_back(self):
        if len(self.node_history) == 1:
            print("Cannot go back any further")
            return
        else:
            self.node_history.pop()
            self.current_node_idx = self.node_history[-1]

    def display_bitmap(self, bitmap):
        if self.interactive:
            print("\033[H\033[J")
            bitmap.show()
        elif self.display_cb is not None:
            self.display_cb(bitmap.content)
        else:
            print("No display callback defined! Skipping Image...")

    def play_audio(self, audio):
        if not self.interactive:
            if self.audio_cb is not None:
                self.audio_cb(audio.content, audio.path)
            else:
                print("No audio callback defined! Defaulting to vlc...")

        audio.play()
        while audio.is_playing:
            time.sleep(0.1)
        audio.release()

        
    def play(self):
        print("{} Playing...".format(self.story.title))
        
        while self.playing:
            current_node = self.story.stage_nodes[self.current_node_idx]

            if current_node.assets['image'] is not None:
                self.display_bitmap(current_node.assets['image'])

            if current_node.assets['audio'] is not None:
                if not self.audio_supressed:
                    self.play_audio(current_node.assets['audio'])  
                self.audio_supressed = False
            else:
                break

            if len(current_node.next_transitions) == 0:
                print("Ran out of nodes?")
                print("Autoplay is {}, attempting to advance to next node".format(current_node.control_settings.autoplay))
                self.current_node_idx += 1
                self.node_history.append(self.current_node_idx)
                continue
                self.playing = False
                continue

            elif len(current_node.next_transitions) == 1:
                self.walk_to_node(current_node.next_transitions[0].to_index)

            else:
                print("Interactive node, please select a transition")

                seek_index = current_node.next_transitions[0].to_index
                options_count = len(current_node.next_transitions)
                min_seek_index = seek_index
                max_seek_index = seek_index + (options_count - 1)

                to_replay_assets = True

                print("You have {} options to chose from".format(options_count))

                controls = self.story.stage_nodes[seek_index].control_settings

                wheel = controls.wheel
                ok = controls.ok
                home = controls.home

                print("Available inputs:", ", ".join([name for name, value in {"wheel": wheel, "ok": ok, "home": home}.items() if value]))

                while True:
                    seek_node = self.story.stage_nodes[seek_index]

                    if to_replay_assets:
                        if seek_node.assets['image'] is not None:
                            self.display_bitmap(seek_node.assets['image'])

                        if seek_node.assets['audio'] is not None:
                            self.play_audio(seek_node.assets['audio'])
                        to_replay_assets = False

                    input_button = self._simulate_input(wheel, ok, home)

                    if input_button == "+":
                        seek_index += 1
                        if seek_index > max_seek_index:
                            seek_index = max_seek_index

                        to_replay_assets = True

                    elif input_button == "-":
                        seek_index -= 1
                        if seek_index < min_seek_index:
                            seek_index = min_seek_index

                        to_replay_assets = True

                    elif input_button == "ok":
                        if len(current_node.next_transitions) == 0:
                            if current_node.control_settings.autoplay:
                                self.walk_to_node(seek_index + 1)
                                break
                            self.playing = False
                            break
                        
                        if len(current_node.next_transitions) == 1:
                            self.walk_to_node(current_node.next_transitions[0].to_index)
                            break
                            
                        self.walk_to_node(seek_index)
                        self.node_history.append(self.current_node_idx)
                        self.audio_supressed = True
                        break
                        

                    elif input_button == "home":
                        if len(current_node.home_transitions) == 0:
                            # No custom home transition available for this node
                            # We just go back to node #0
                            self.reset_to_node(0)
                            break
                        else:
                            home_transition = current_node.home_transitions[0]
                            self.walk_to_node(home_transition.to_index)
                            break

        print("Story ended.")

    def feed_input(self, button):
        if button == "wheel":
            self.pending_input = "+"
        elif button == "ok":
            self.pending_input = "ok"
        elif button == "home":
            self.pending_input = "home"
        elif button == "wheel":
            self.pending_input = "-"
        else:
            return False
        return True

    def _simulate_input(self, wheel, ok, home):
        if not self.interactive:
            user_input = self.pending_input
        else:
            user_input = input("Lunii> ").lower().strip()
        if wheel and user_input == "+":
            return "+"
        elif ok and user_input == "ok":
            return "ok"
        elif home and user_input == "home":
            return "home"
        elif wheel and user_input == "-":
            return "-"
        else:
            if not self.interactive:
                # avoid a busy loop
                time.sleep(0.2)
            print("Invalid input")
            return self._simulate_input(wheel, ok, home)
