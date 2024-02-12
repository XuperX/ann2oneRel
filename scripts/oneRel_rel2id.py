# the OneRelDB also requires a rel2id.json file.

import os
import json
import shutil
import argparse


def getRel2id(dirs):
    uniq_rels = []
    for corpus_dir in dirs:
        one_rel_aggregated_file = os.path.join(corpus_dir, "all_pub.json")


        with open(one_rel_aggregated_file) as infile:
            one_rel_aggregated = json.load(infile)
        for one_sent in one_rel_aggregated:
            for triple in one_sent["triple_list"]:
                if triple[1] not in uniq_rels:
                    uniq_rels.append(triple[1])

    rel: object
    id2rel = {str(i): rel for i, rel in enumerate(uniq_rels)}
    rel2id = {rel: i for i, rel in enumerate(uniq_rels)}
    final = [id2rel, rel2id]
    return final

parser = argparse.ArgumentParser()
parser.add_argument("--target_dir", type=str, help="The directory of the corpus")

args = parser.parse_args()
corpus_dir = args.target_dir
dirs = [os.path.join(corpus_dir,'train'), os.path.join(corpus_dir,'dev'), os.path.join(corpus_dir,'test')]

# move to the oneRel directory
for corpus_dir in dirs:
    dataset_dir = os.path.join("outputs/",corpus_dir.split("/")[-2])
    os.makedirs(dataset_dir, exist_ok=True)
    which_file = str(corpus_dir.split("/")[-1])
    output_dir = "outputs/"+which_file
    shutil.copy(os.path.join(corpus_dir, "all_pub.json"), os.path.join(dataset_dir,which_file + "_triples.json"))
    with open(os.path.join(dataset_dir,"rel2id.json"), "w") as outfile:
        json.dump(getRel2id([corpus_dir]), outfile, indent=4)