# Lumiios

Lumiios is a Python program that allows you to manage and emulate the Lunii StoryTeller. With Lumiios, you can easily parse every story in your device and get details about each one.

- [Installation](#installation)
- [Usage](#usage)
  - [Device-level methods](#device-level-methods)
  - [Story-level methods](#story-level-methods)
  - [Playing stories](#playing-stories)
- [Contributing](#contributing)

## Installation

Lumiios is available under PyPi! You can install it by:
```bash
pip install lunii
```

Or alternatively you can:
```bash
pip install git+https://github.com/bastien8060/Lumiios
```

## Usage

### Device-level methods
To use Lumiios, you need to create an instance of the Device class by passing in the folder mountpoint or dump location of your Lunii StoryTeller. Once you have a Device instance, you can call its methods to get information about the stories on your device.

```python
from lunii import Device

device = Device('/media/lunii')

# get the serial number of the Lunii StoryTeller
snu = device.snu

# get the major and minor firmware version of the Lunii StoryTeller
fw_vers_major = device.fw_vers_major
fw_vers_minor = device.fw_vers_minor

print(f'Lunii StoryTeller SNU: {snu}')
print(f'Lunii StoryTeller Firmware Version: {fw_vers_major}.{fw_vers_minor}')
```

### Story-level methods

You can also parse the stories on your device and get information about each one, as well as read them fully in the next release.

```python
# parse all stories
device.parse_stories()

story = device.stories[0]

version = story.version
title = story.title
authorized = story.authorized # True if story is authorized by the Lunii StoryTeller (checksum is valid)
night_mode = story.night_mode # True if the story is Night Mode compatible

if authorized:
    print(f'Version: {version}')
    print(f'Title: {title}')
    print(f'Night Mode: {night_mode}')
else:
    print(f'Story {title} is not authorized')

```

You can also parse a single story by passing in the UUID of the story. This is useful if you have a lot of stories on your device.

```python
# get the list of stories installed on the Lunii StoryTeller
story_uuid = device.story_list[0]

# parse a single story
story = device.parse_story(story_uuid)
```

Lumiios also allows you to read the cover audio of a story. 

```python
# get the cover audio of a story
cover_audio = story.cover_audio

print(f'Cover audio content type: {cover_audio.audio_type}')

print('Playing cover audio...')
cover_audio.play()
while cover_audio.is_playing():
    time.sleep(0.1)
cover_audio.release()


# saving it
with open('cover_audio.mp3', 'wb') as f:
    f.write(cover_audio.content)
```

### Playing stories

Lumiios also allows you to play stories on your Lunii StoryTeller. This is done by creating a StoryPlayer instance with a Story instance. You can then play the story by calling the play() method.

```python
from lunii import StoryPlayer

story_player = StoryPlayer(story)
# this will block until the story is finished playing
story_player.play()

print("Player History: {}".format(story_player.node_history))
```
Or you can interact with the story programmatically by passing interactive=False and callbacks to the StoryPlayer constructor.

```python

def display_cb(image:ImageAsset):
    with open('image.png', 'wb') as f:
        f.write(image.content)
    # or display the image in a terminal: image.show()

def audio_cb(audio:AudioAsset):
    with open('audio.mp3', 'wb') as f:
        f.write(audio.content)
    # or play the audio with vlc: audio.play()

story_player = StoryPlayer(story, interactive=False, display_cb=display_cb, audio_cb=audio_cb)
story_player.play() # blocks until the story is finished playing
```

you can run the play() method in a separate thread to allow the story to play in the background. These are the methods you can use to interact with the story:

```python
from lunii.utils import Buttons

story_player.play() # starts playing the story
story_player.walk_back() # goes back to the previous node
reset_to_node(0) # resets the story to the node #0 so the start of the story
story_player.playing # returns True if the story is playing and False if it has finished 

buttons = [Buttons.PLUS, Buttons.MINUS, Buttons.HOME, buttons.OK]
story_player.feed_input(buttons[0]) # feeds the story with the buttons pressed
```


> Note: The StoryPlayer class is still in development and is not fully functional yet.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

If you find a bug or have a feature request, please open an issue on GitHub.

If you want to contribute to Lumiios, please open a pull request on GitHub.

