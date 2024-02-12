"""
To make sure my database has consistent quality, I'd like to extract them to manually exam what are the keys(labels),
what are the values, and what are the surrounding context.

|term id| label| text| attribute if any| words around it if any|

"""

import os
import pandas as pd
import json
from collections import Counter
import spacy
import re
import argparse
import sys
import datetime

def getAnnFiles(target_dir):
    ann_files = []
    for file in os.listdir(target_dir):
        if file.endswith(".ann"):
            ann_files.append(file)
    return ann_files
def deleteNullJson(json_obj):
    # the json_obj is a list of dictionaries. each dictionary is a term.
    new_json = []
    for term in range(len(json_obj)):
        new_term = {}
        for key, value in json_obj[term].items():
            if value is not None:
                if len(value) > 0:
                    new_term[key] = value
        new_json.append(new_term)
    return new_json
def getSentenceIndex(pmcid, target_dir, spacy_model="en_core_sci_sm"):
    # given pmc file, figure out the sentence start and sentence end so that we can find out which sentence the term locates.
    # return a dictionary with sentence start and sentence end.
    with open(os.path.join(target_dir, pmcid + ".txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    nlp = spacy.load(spacy_model)
    doc = nlp(content)
    sentences = list(doc.sents)
    sents_dic = []
    for sent in sentences:
        sent_dic = {}
        sent_dic["start"] = sent.start_char
        sent_dic["end"] = sent.end_char
        sent_dic["text"] = sent.text
        sents_dic.append(sent_dic)
    return sents_dic
def getTermSentence(term_df, sents_dic):
    # given a term, find out which sentence it belongs to.
    # return the term_df adding a column "sentence_text"
    # sents_dic = [{"start": 0, "end": 10, "text": "this is a sentence"}, {"start": 11, "end": 20, "text": "this is another sentence"}]
    # term_df = {"start": 5, "end": 8, "text": "is"}
    for idx, term in term_df.iterrows():
        for sent in sents_dic:
            if int(term["start"]) >= int(sent["start"]) and int(term["end"]) <= int(sent["end"]):
                term_df.loc[idx, "sentence_text"] = sent["text"]
    return term_df
def loadAnns(target_dir, ann_file,spacy_model="en_core_sci_sm"):
    """
    Etract alll annotations into the file format. there are four types of annotations
    1. terms
    2. attributes
    3. stars
    4. relationships
    5. notes
    AND save them in terms.
    Things need to be extracted
    1. all terms in json (all ttributes merged into terms)
    2. all relationships in json
    3. report the number of terms, attributes, stars, relationships, notes
    4. report number of lines note extracted.
    """

    with open(os.path.join(target_dir, ann_file), 'r', encoding='utf-8') as file:
        ann_content = file.readlines()
    pmc = ann_file.split(".")[0]

    # get all terms
    terms_tsv = [line.strip().split('\t') for line in ann_content  if line.startswith('T')]
    terms_df = pd.DataFrame(terms_tsv, columns=['t_id', 'annos', 'text'])
    terms_df[['label','start', 'end']] = [loc.split(" ") for loc in terms_df['annos']]
    terms_df = terms_df.drop(columns=['annos'])

    stars = [line.strip().split('\t') for line in ann_content if line.startswith('*')]
    # todo there is a bug, ['*', 'PartOf T8 T9 T10']
    if stars:
        stars_df = pd.DataFrame(stars, columns=['s_id', 's_details'])
        new_stars_df = pd.DataFrame(columns=['s_type', 'arg1', 'arg2'])
        for star_indx in range(len(stars_df)):
            if len(stars_df.loc[star_indx, 's_details'].split(" ")) == 3:
                new_stars_df.loc[len(new_stars_df)] = stars_df.loc[star_indx, 's_details'].split(" ")
        stars_df = new_stars_df

    # relationships
    rels = [line.strip().split('\t') for line in ann_content  if line.startswith('R')]
    rels_df = pd.DataFrame(rels, columns=['rel_id', 'rel_details'])
    rels_df[['rel_type','arg1', 'arg2']] = [rel.split(" ") for rel in rels_df['rel_details']]
    rels_df = rels_df.drop(columns=['rel_details'])
    rels_df['arg1'] = [value.split(":")[1].strip() for value in rels_df['arg1']]
    rels_df['arg2'] = [value.split(":")[1].strip() for value in rels_df['arg2']]

    if stars:
        for idx in range(len(stars_df)):
            rels_df.loc[len(rels_df)+idx] = stars_df.loc[idx]

    # add term details to the relationships
    rels_df = rels_df.merge(terms_df, left_on='arg1', right_on='t_id', how='left')
    rels_df = rels_df.rename(columns={'label':'arg1_label', 'text':'arg1_text', 'start':'arg1_start', 'end':'arg1_end'})
    rels_df = rels_df.drop(columns=['t_id'])
    rels_df = rels_df.merge(terms_df, left_on='arg2', right_on='t_id', how='left')
    rels_df = rels_df.rename(columns={'label':'arg2_label', 'text':'arg2_text', 'start':'arg2_start', 'end':'arg2_end'})
    rels_df = rels_df.drop(columns=['t_id'])

    #rels_json = json.loads(rels_df.to_json(orient='records'))
    #rels_json = deleteNullJson(rels_json)
    #with open(os.path.join(target_dir, pmc + "_rels.json"), 'w', encoding='utf-8') as file1:
        #json.dump(rels_json, file1)

    # two types of attributes, yes/no or pick one value.
    try:
        attrs = [line.strip().split('\t') for line in ann_content  if line.startswith('A')]
        attrs_df = pd.DataFrame(attrs, columns=['a_id', 'attrs'])
        for attr_indx in range(len(attrs_df)):
            if len(attrs_df.loc[attr_indx, 'attrs'].split(" ")) == 2:
                new_value = attrs_df.loc[attr_indx, 'attrs'] + " True"
                attrs_df.loc[attr_indx, 'attrs'] = new_value

        attrs_df[["attrType", 'term', 'attrValue']] = [attr.split(" ") for attr in attrs_df['attrs']]
        attrs_df = attrs_df.drop(columns=['attrs'])
        terms_df = terms_df.merge(attrs_df, left_on='t_id', right_on='term', how='left')
    except:
        pass

    terms_df = terms_df.merge(rels_df, left_on='t_id', right_on='arg1', how='left')

    # add surrounding text
    with open(os.path.join(target_dir,pmc + ".txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    # add sentence index
    sent_idx = getSentenceIndex(pmc, target_dir,spacy_model)
    terms_df = getTermSentence(terms_df, sent_idx)

    terms_df = terms_df.rename(columns={'t_id_x':'t_id','label_x':'label', 'text_x':'text', 'start_x':'start', 'end_x':'end'})
    terms_df = terms_df.rename(columns={'label_y':'arg_label', 'text_y':'arg_text', 'start_y':'arg_start', 'end_y':'arg_end'})
    terms_json = json.loads(terms_df.to_json(orient='records'))
    terms_json = deleteNullJson(terms_json)
    with open(os.path.join(target_dir, pmc + "_terms.json"), 'w', encoding='utf-8') as file:
        json.dump(terms_json, file, indent=4)
    extraction_status = [0] * len(ann_content)
    for line in range(len(ann_content)):
        if ann_content[line].startswith('T'):
            extraction_status[line] = "Terms"
        elif ann_content[line].startswith('A'):
            extraction_status[line] = "Attributes"
        elif ann_content[line].startswith('Eq'):
            extraction_status[line] = "stars"
        elif ann_content[line].startswith('R'):
            extraction_status[line] = "Relationships"
        elif ann_content[line].startswith('#'):
            extraction_status[line] = "Notes"
        elif ann_content[line].startswith('E'):
            extraction_status[line] = "Events"
    for line in range(len(ann_content)):
        if extraction_status[line] == 0:
            extraction_status[line] = "Not extracted"

    stat_check = dict(Counter(extraction_status))
    if "Not extracted" in stat_check.keys():
        if "Events" in stat_check.keys():
            if stat_check["Events"] == stat_check["Not extracted"]:
                pass
            else:
                stat_check["Not extracted"] = stat_check["Not extracted"] - stat_check["Events"]
        print("Warning: not extracted: ", stat_check["Not extracted"], "out of", len(ann_content))
        print(stat_check)
    else:
        print(f"\033[92mAll extracted\033[0m")
    return terms_df, rels_df

def main():

    parser = argparse.ArgumentParser(description='Ann to json')
    parser.add_argument('--target_dir', type=str, help='target directory')
    parser.add_argument('--spacy_model', type=str, default="en_core_sci_sm", help='spacy model')
    parser.add_argument('--debug', type=bool, help='debug',default=False)

    args = parser.parse_args()

    target_dir  = args.target_dir
    spacy_model = args.spacy_model
    debug = args.debug

    now = datetime.datetime.now()
    logFile = now.strftime("log_%Y-%m-%d_%H-%M-%S"+"_ann2json.log")

    original_stdout = sys.stdout
    with open(logFile, 'w') as f:
        sys.stdout = f

        sub_dirs = ["train", "dev", "test"]
        for sub_dir in sub_dirs:
            print("\n ---------Processing-------------\n", sub_dir)
            target_subdir = os.path.join(target_dir,sub_dir)
            ann_files = getAnnFiles(target_subdir)
            for ann_file in ann_files:
                print(ann_file)
                if debug:
                    terms_df, rels_df = loadAnns(target_subdir, ann_file, spacy_model)
                    getSentenceIndex(ann_file.split(".")[0], target_subdir, spacy_model)
                else:
                    try:
                        terms_df, rels_df = loadAnns(target_subdir, ann_file, spacy_model)
                        getSentenceIndex(ann_file.split(".")[0], target_subdir, spacy_model)
                    except:
                        print(f"\033[91m error in \033[0m", ann_file)
        sys.stdout = original_stdout
        f.close()
if __name__ == "__main__":
    main()
