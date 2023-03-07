import time
from typing import List

class StoryPlayer:
    def __init__(self, story):
        self.story = story
        self.current_node_idx = 0
        self.audio_supressed = False
        self.playing = True
        self.node_history = [0]
    
    def walk_back(self):
        if len(self.node_history) == 1:
            print("Cannot go back any further")
            return
        else:
            self.node_history.pop()
            self.current_node_idx = self.node_history[-1]
        
    def play(self):
        print("{} Playing...".format(self.story.title))
        
        while self.playing:
            current_node = self.story.stage_nodes[self.current_node_idx]

            if current_node.assets['image'] is not None:
                print("\033[H\033[J")
                current_node.assets['image'].show()

            if current_node.assets['audio'] is not None:
                if not self.audio_supressed:
                    current_node.assets['audio'].play()
                    while current_node.assets['audio'].is_playing:
                        time.sleep(0.1)
                    current_node.assets['audio'].release()
                self.audio_supressed = False
            else:
                break

            if len(current_node.next_transitions) == 0:
                print("Ran out of nodes?")
                if current_node.control_settings.autoplay:
                    print("Autoplay is enabled, attempting to advance to next node")
                    self.current_node_idx += 1
                    self.node_history.append(self.current_node_idx)
                self.playing = False
                continue

            elif len(current_node.next_transitions) == 1:
                self.current_node_idx = current_node.next_transitions[0].to_index
                self.node_history.append(self.current_node_idx)

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
                            print("\033[H\033[J")
                            seek_node.assets['image'].show()

                        if seek_node.assets['audio'] is not None:
                            seek_node.assets['audio'].play()
                            while seek_node.assets['audio'].is_playing:
                                time.sleep(0.1)
                            seek_node.assets['audio'].release()
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
                        self.current_node_idx = seek_index
                        self.node_history.append(self.current_node_idx)
                        break

                    elif input_button == "home":
                        if len(current_node.home_transitions) == 0:
                        # No custom home transition available for this node
                        # We just go back to node #0
                        current_node_idx = 0
                        self.node_history = [0]
                        break
                    else:
                        home_transition = current_node.home_transitions[0]
                        current_node_idx = home_transition.to_index
                        self.node_history.append(current_node_idx)
                        break

        print("Story ended.")

    def _simulate_input(self, wheel, ok, home):
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
            print("Invalid input")
            return self._simulate_input(wheel, ok, home)
