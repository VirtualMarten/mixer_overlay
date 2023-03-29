# Simple Audio Mixer Overlay
A simple volume overlay I built for use with my XP-PEN tablet buttons and wheel.

<img alt="XP-PEN Artist 12 Pro with my audio mixer on the screen" src="https://user-images.githubusercontent.com/110787538/228394032-44c5c653-2218-45c8-b4e3-5abe2e531f09.jpg" width="300">

[demo.webm](https://user-images.githubusercontent.com/110787538/228394630-b0862a7c-c06e-42c1-8250-1fdc60202a6f.webm)

This uses the WIN32 API so will only work on Windows, tested on Windows 10.
I want to eventually rebuild this in C++ with a dedicated process to listen for a key combo to open the mixer.

## Setup

### 1. Install dependecies
I included a "dependecies.txt" with all the required python modules. You can install them with `pip install -r dependencies.txt`.

### 2. (Optional) Build into an EXE using pyinstaller or similar.
I included a "build.bat" file for wrestling the python app into a semi portable EXE in "./bin". That makes the next step easier.

### 3. AutoHotKey
I included the AutoHotKey script I use for opening the overlay. You can find AutoHotKey here: https://www.autohotkey.com/
I personally compiled the script into an EXE and put a shortcut to it in my windows Startup folder.
You can compile an AutoHotKey script by right clicking the script in file exploror, and clicking "Compile Script".
You can find your startup apps folder by pressing Win+R and entering "shell:startup".

### 4. Key Bindings for your drawing tablet or other input device.
For my XP-PEN Artist 12 Pro, I set each button to select a volume slider, and I set the wheel to turn the volume up and down.
The target application is set to the EXE created by pyinstaller in step 2.

Button bindings:

![XP-PEN configuration software button bindings](https://user-images.githubusercontent.com/110787538/228394248-cf2cd5ff-1d0f-4e24-9d92-98db63d40445.png)

Wheel bindings:

![XP-PEN configuration software wheel bindings](https://user-images.githubusercontent.com/110787538/228394251-e16d1363-0ffb-4b4f-b30f-ba091fa7d792.png)

## Keyboard Bindings

- *1-9*: Selects the control in that position.
- *Up and Down*: Turns the volume of selected control up or down.
- *Escape*: Closes the overlay.

## Configuration

### `debug`
- Type: Boolean
- Default: False
Enable or disable debug output.
This includes verbose application names on the volume control sliders.

### `monitor`
- Type: Integer
- Default: 1
The monitor you want the overlay to display on, starting at 0 or monitor 1.

### `button_count` or `control_count`
- Type: Integer
- Default: 8
The amount of buttons your device has, in the case of my Artist 12 Pro drawing tablet, I have 8.

### `close_on_deselect`
- Type: Boolean
- Default: True
If the overlay should automatically close when it looses focus.

### `steam_library_folders`
- Type: List of Strings
- Default: `[ path.join(environ["ProgramFiles(x86)"], 'Steam') ]`
A list of steam library folder paths.

### `steam_game_cache_timeout`
- Type: Integer
- Default: 7200
In minutes, the amount of time it takes for the steam game cache to be invalidated.
NOTE: The steam game cache is also the index the overlay uses for determining if an app is a steam game.
Depending on how many steam games you have it could take a long time to build this index.

### `steam_game_cache_file`
- Type: String
- Default: "games.cache"
Path to the steam game cache cache file.

### `steamapp_exlusions`
- Type: List of Strings
A list of regular expressions to exclude from the steam games list. This is appended to the built in exclusions.

### `override_steamapp_exlusions`
- Type: Boolean
- Default: False
If set to true, your steamapp_exclusions list will override the built in exclusions entirely.

### `fg_color`
- Type: String
- Default: "#111"
The default control foreground color.

### `bg_color`
- Type: String
- Default: "#eee"
The default control background color.

### `show_process_count`
- Type: Boolean
- Default: True
If a volume control is controlling multiple processes, show the amount.

### `min_width`
- Type: Integer
- Default: 432
The minimum width for the volume controls in pixels.

### `spacer_position`
- Type: Integer
- Default: 0
If larger than 0, insert a spacer at that control index.

### `auto_fill`
- Type: Boolean
- Default: True
Automatically populate empty button slots with the volume control specified by "auto_fill_control".

### `auto_fill_control`
See Control Configuration.

### `controls`
- Type: List of Objects
See Control Configuration.

## Control Configuration
A control can capture a process or a bunch of processes, and allows you to control their volume.

### `name`
- Type: String
- Default: "Control <n>"
The name of the control.

### `target_applications`
- Type: List of Strings
A list of process names that this control will control the volume of.
If `<all>` this control matches all processes.
If `<steamgame>` this control matches all steam games.
If starts with `r\`` it will be treated as a regular expression.
If starts with `~` it will search for the string in the process name.

### `use_app_title`
- Type: Boolean
- Default: False
if true, use the window title of the target application for this control.

### `use_app_name`
- Type: Boolean
- Default: False
If true, use the name specified above for this control.

### `only_first`
- Type: Boolean
- Default: False
If true, this volume control will only control the volume of the first matched process.

### `master`
- Type: Boolean
- Default: False
If true, this control is a master volume control.

### `fg_color`
- Type: String
The control foreground color.

### `bg_color`
- Type: String
The control background color.

### `bg_color2`
- Type: String
If specified, this turns the background into a gradient from bg_color to bg_color2.
