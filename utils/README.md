# Utils

数据标注之前先用 **[audio-slicer](https://github.com/openvpi/audio-slicer)** 切分一下音频数据，得到一些 10s 左右的 wav 文件后，可以考虑用 **[
whisper](https://github.com/openai/whisper)** 转录为拼音，再使用 MinLabel 检查纠错。

## transcribe.py

识别语音的脚本，需要安装 pytorch 和 whisper 环境（最好用GPU）