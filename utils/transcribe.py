import os
import sys
import glob
import whisper
from tqdm import tqdm
from pypinyin import lazy_pinyin


def transcribe(path):
    if not os.path.isdir(path):
        print("illegal path!")
        return
    model = whisper.load_model("large")

    files = list(glob.glob(os.path.join(path, "*.wav")))
    pbar = tqdm(files)
    for file_name in pbar:
        lab_name = file_name[:-3] + "lab"
        if os.path.exists(lab_name):
            # print(lab_name, "exists")
            continue
        # print(file_name)
        result = model.transcribe(file_name, language="chinese")
        text = result["text"]
        if not isinstance(text, str):
            continue
        pbar.write(f"{text} {lazy_pinyin(text)}\n")
        with open(lab_name, "w", encoding="utf-8") as f:
            f.write(" ".join(lazy_pinyin(text)))


if __name__ == "__main__":
    # set default path here
    path = r""
    if len(sys.argv) >= 2:
        path = sys.argv[1]
    transcribe(path)
    