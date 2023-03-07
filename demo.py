import io
import os
import struct
import random
import uuid

from Lunii import Lunii
from Story import Story

from pprint import pprint
import time
      

def pretty_print_story(story):
    print('-' * 50)

    # print a table with relevant infos about the story
    print("Story Title: {}".format(story.title))
    print("Story UUID: {}".format(story.uuid))
    print("Story Version: {}".format(story.version))
    print("Story Authorized: {}".format(story.authorized))
    print("NightMode Supported: {}".format(story.night_mode))

    # print separator
    print('-' * 50)

    """
    Very Handy Node Debugging
    print("Story Nodes:")
    for node_idx in story.stage_nodes:
        node = story.stage_nodes[node_idx]
        print("Node ID: {}".format(node.index))

        image = node.assets['image']
        audio = node.assets['audio']
        print("Node Image: {}".format(image))
        print("Node Audio: {}".format(audio))

        if node.next_transitions:
            print("Node OK Transition: \n\tcount: {}".format(len(node.next_transitions)))
        if node.home_transitions:
            print("Node Home Transition: \n\tallowed: {}".format(True if node.home_transitions else False))

        controls = node.control_settings
        wheel, ok, home, pause, autoplay = controls.wheel, controls.ok, controls.home, controls.pause, controls.autoplay
        print("Node Control Settings: \n\twheel: {}\n\tok: {}\n\thome: {}\n\tpause: {}\n\tautoplay: {}".format(wheel, ok, home, pause, autoplay))

        print('-' * 50)
    """
        

# To be honest, this function is poorly written... I just wanted to get it working quickly
def play_story(story):
        
    print("{} Playing...".format(story.title))

    # We begin a loop that will play the story
    # Each round we update the current node, and play the audio and image
    # We prefer to keep the node in memory by its index, so it is easier to process generally, programatically-wise

    playing = True
    current_node_idx = 0
    audioSupressed = False

    while playing:
        # We fetch the current node obj, from it's index
        current_node = story.stage_nodes[current_node_idx]

        # it is possible that the node has no image or audio, so we check for that
        if current_node.assets['image'] is not None:
            print("\033[H\033[J") # clear screen
            current_node.assets['image'].show() # we call the show method of the ImageAsset object, defined in the utils.py

        if current_node.assets['audio'] is not None:
            if not audioSupressed:
                current_node.assets['audio'].play() # Utils.py: AudioAsset.play()
                # we wait for the audio to finish playing, since VLC is async in python
                # I am probably doing this wrong, because I notice audio cuts occasionally using VLC,
                # (only for short audio files)
                # but it is the only thing that would work under WSL2 (Windows Subsystem for Linux)
                # Take this as a quick POC
                while current_node.assets['audio'].is_playing:
                    time.sleep(0.1) 
                current_node.assets['audio'].release()
            audioSupressed = False
        else:
            break
        

        # We check if the node has any transitions

        # if it has no transitions, we have reached the end of the story
        if len(current_node.next_transitions) == 0:
            print("Ran out of nodes?")
            if current_node.control_settings.autoplay:
                print("Autoplay is enabled, attempting to advance to next node")
                current_node_idx += 1
            playing = False
            continue

        # if it has one transition, we can just skip on to the next node,
        # without requiring any user input (Simple StageNode)
        elif len(current_node.next_transitions) == 1:
            current_node_idx = current_node.next_transitions[0].to_index

        # if it has more than one transition, we need to ask the user for input, 
        # That would mean we hit an ActionNode
        else:
            print("Interactive node, please select a transition")
            
            # Since we aren't running on a real Lunii, we need to simulate the various inputs
            # input simulation map:
            """
            "+"     -> increment wheel (clockwise)
            "-"     -> decrement wheel (counter-clockwise)
            "ok"    -> ok button
            "home"  -> home button
            """
            # We loop until we have found a node to transition to
            # This is like a console. For simplicity, we don't actually update the current node index,
            # but we create a new variable to hold the index of the node we are seeking at (options in the story to choose from)
            unresolved_input = True

            # We start by setting the seek index to the first option in the list
            # We also define what is the highest and lowest index we can seek at
            # This is to prevent the user from going out of bounds
            # The range in between are the indexes of the options we can select
            seek_index = current_node.next_transitions[0].to_index
            options_count = len(current_node.next_transitions)
            min_seek_index = seek_index
            max_seek_index = seek_index + (options_count - 1)

            # For later, this will be described down below
            to_replay_assets = True

            print("You have {} options to chose from".format(options_count))

            # We fetch the control settings for the current node
            # Aka, what are the inputs/buttons possible (like permitted) for this node
            controls = story.stage_nodes[seek_index].control_settings # Utils.py:ControlSettings

            # We check if we can use the wheel, the ok button, and the home button
            wheel = controls.wheel
            ok = controls.ok
            home = controls.home
            

            print("Available inputs:", ", ".join([name for name, value in {"wheel": wheel, "ok": ok, "home": home}.items() if value]))

            # We loop until we have resolved the input
            while unresolved_input:
                # We fetch the node we are seeking at, by its index
                seek_node = story.stage_nodes[seek_index]

                # We only replay the assets if we have changed the seek index
                # this is to prevent the assets from being replayed every time we ask for input, 
                # when the user has given an invalid input, which would be annoying
                if to_replay_assets:
                    # We show the image of the node we are seeking at
                    if seek_node.assets['image'] is not None:
                        print("\033[H\033[J") # clear the console
                        seek_node.assets['image'].show()

                    # as well as play its audio
                    if seek_node.assets['audio'] is not None:
                        seek_node.assets['audio'].play()
                        while seek_node.assets['audio'].is_playing:
                            time.sleep(0.1)
                        seek_node.assets['audio'].release()
                    to_replay_assets = False

                # We ask the user for input (simulates button presses)
                user_input = input("Lunii> ").lower().strip()
                if user_input == '+' and wheel:
                    if seek_index == max_seek_index:
                        print("Can't seek further")
                        continue
                    seek_index += 1
                    to_replay_assets = True

                elif user_input == '-' and wheel:
                    if seek_index == min_seek_index:
                        print("Can't seek lower")
                        continue
                    seek_index -= 1
                    to_replay_assets = True

                elif user_input == 'ok' and ok:
                    # we check if the node we are seeking at has any transitions
                    if len(seek_node.next_transitions) == 0:
                        # If so, it becomes a bit more complicated...
                        # Sigh, here we go:
                        # If we ran out of transitions, we can't fetch any new nodes, 
                        # so we check if autoplay is enabled
                        if current_node.control_settings.autoplay:
                            # Autoplay is enabled, we can just have go to the next node
                            current_node_idx = seek_index + 1
                        else:
                            # Autoplay is disabled, we can't go to the next node
                            # So we just stop playing, story is over
                            playing = False
                        # Either way, we can leave the loop:
                        unresolved_input = False
                        continue

                    # Otherwise, happy days, we can just fetch a transition, and get the next node
                    seek_node = story.stage_nodes[seek_index]

                    if len(seek_node.next_transitions) == 1:
                        transition = seek_node.next_transitions[0]
                        current_node_idx = transition.to_index
                    else:
                        audioSupressed = True 
                        current_node_idx = seek_index

                    """
                    TODO: Check if the next node is an ActionNode
                    Notice how I don't count the numbers of Transitions, and skip to the first transition?
                    Because of the way I programmed this, it would just skip checking if there are multiple options
                    and just go to the first one, which is not what we want in some cases
                    For example, les incollables CE1 does have multiple ActionNodes in a row,
                    This implementation assumes that the next node is a SimpleNode, which is not always the case
                    This can sometimes cause the reader to mess up the story (e.g Les incollables CE1)
                    I didn't think of this when I wrote this, and I don't have the time to rewrite this right now
                    """

                    unresolved_input = False

                elif user_input == 'home' and home:
                    if len(current_node.home_transitions) == 0:
                        # No custom home transition available for this node
                        # We just go back to node #0
                        current_node_idx = 0
                    else:
                        home_transition = current_node.home_transitions[0]
                        current_node_idx = home_transition.to_index
                    unresolved_input = False
                else:
                    print("Invalid command, try again") 
                    continue



def main():
    client = Lunii('./Image') # ./Image is the path to the folder where rootfs is mounted at/extracted to

    print("FW Version: {}.{}".format(client.fw_vers_major, client.fw_vers_minor))
    print("SNU: {}".format(client.snu))

    # get random story uuid, from the PI
    story_uuid = random.choice(client.story_list)

    # get story object,
    # this will parse the story, and decrypt the assets 
    story = client.parse_story(uuid=story_uuid)

    # print story info
    # Just for debugging purposes
    pretty_print_story(story)

    # play story
    play_story(story)

if __name__ == '__main__':
    main()
