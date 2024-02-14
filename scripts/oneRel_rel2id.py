# the OneRelDB also requires a rel2id.json file.

import os
import json
import shutil
import argparse
from print_color import print

def getRel2id(output_dir):
    unique_rels = []
    for file in os.listdir(output_dir):
        if file.endswith("_triples.json"):
            with open(os.path.join(output_dir, file), "r") as f:
                sents_obj = json.load(f)
                for sent_obj in sents_obj:
                    if len(sent_obj["triple_list"]) == 0:
                        unique_rels.append("")
                    else:
                        for triple in sent_obj["triple_list"]:
                            print(triple,color="red")
                            if len(triple)>0:
                                if triple[1] not in unique_rels:
                                    unique_rels.append(triple[1])
    id2rel = {str(i): rel for i, rel in enumerate(unique_rels)}
    rel2id = {rel: i for i, rel in enumerate(unique_rels)}
    final = [id2rel, rel2id]
    return final

parser = argparse.ArgumentParser()
parser.add_argument("--target_dir", type=str, help="The directory of the corpus")

args = parser.parse_args()
corpus_dir = args.target_dir
dirs = [os.path.join(corpus_dir,'train'), os.path.join(corpus_dir,'dev'), os.path.join(corpus_dir,'test')]


for corpus_dir in dirs:
    dataset_dir = os.path.join("outputs/",corpus_dir.split("/")[-2])
    os.makedirs(dataset_dir, exist_ok=True)
    which_file = str(corpus_dir.split("/")[-1])
    output_dir = "outputs/"+which_file
    shutil.copy(os.path.join(corpus_dir, "all_triples.json"), os.path.join(dataset_dir,which_file + "_triples.json"))

output_dir = "outputs/"+corpus_dir.split("/")[1]
os.makedirs(output_dir, exist_ok=True)
rel2id = getRel2id(output_dir)
with open(os.path.join(output_dir, "rel2id.json"), "w") as f:
    json.dump(rel2id, f, indent=4)


