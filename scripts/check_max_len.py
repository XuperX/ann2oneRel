import os
import json

dir = "outputs/corpus3"
files = [f for f in os.listdir(dir) if f.endswith("_triples.json")]
max_len = 0
for file in files:
    with open(os.path.join(dir, file)) as infile:
        data = json.load(infile)
        for item in data:
            if len(item["text"]) > max_len:
                max_len = len(item["text"])
print(max_len)