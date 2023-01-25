# MinLabel

MinLabel is a voice label tool based on Tkinter in Python3.

## How to Use

open folder -> select a wav file on the list -> edit the label content -> press `replace` to write to the lab file

<img src="docs\example.png" alt="example" style="zoom:100%;" />

## Features

- play audio samples
- delete wav file and lab file if the audio is useless (**make sure you have a backup in case of accidental deletion**)
- use `Status` to show whether a sample is ready or not
- Press `i` to focus on the label text area
- Press `Ctrl + s` to save your label
- Press `Alt + z` to select the next wav file

## Installation

Install the module with pip:

```
pip install -r requirements.txt
```

run `minlabel.py`:

```
python minlabel.py
```

## TODO

- Optimize the UI
