# Lumiios

Lumiios is a Python program that allows you to manage and emulate the Lunii StoryTeller. With Lumiios, you can easily parse every story in your device and get details about each one.

## Installation

```bash
pip install lunii
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

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

If you find a bug or have a feature request, please open an issue on GitHub.

If you want to contribute to Lumiios, please open a pull request on GitHub.

