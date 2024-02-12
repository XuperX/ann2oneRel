# the OneRelDB also requires a rel2id.json file.

import os
import json
import shutil

dirs = ['../data/corpus_v3/train', '../data/corpus_v3/dev', '../data/corpus_v3/test']

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

# move to the oneRel directory
for corpus_dir in dirs:
    which_file = corpus_dir.split("/")[-1]
    oneRel_dir = "/Users/user/myPhD_code_git/20240106_oneRel_code/OneRel/Data/CorpusV3/"
    shutil.copy(os.path.join(corpus_dir, "all_pub.json"), oneRel_dir+which_file + "_triples.json")
    with open (os.path.join(oneRel_dir,"rel2id.json"), "w") as outfile:
        json.dump(getRel2id([corpus_dir]), outfile, indent=4)