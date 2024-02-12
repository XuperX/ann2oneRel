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

def getTextWindow(terms_df, content, window_size=25):
    # terms_df: all terms extracted per arctile in the dataframe.
    # content: the text content of the article
    # window_size: HALF of the number of words around the term to be extracted.
    # return: a dataframe with the term, the text, and the window around the term.
    for index, term in terms_df.iterrows():
        window_start = int(term["start"]) - window_size if int(term["start"]) - window_size > 0 else 0
        window_end = int(term["end"]) + window_size if int(term["end"]) + window_size < len(content) else len(content)
        text_window = content[window_start:window_end]
        terms_df.loc[index, "text_window"] = text_window
    return terms_df
def getSentenceIndex(pmcid, target_dir):
    # given pmc file, figure out the sentence start and sentence end so that we can find out which sentence the term locates.
    # return a dictionary with sentence start and sentence end.
    with open(os.path.join(target_dir, pmcid + ".txt"), 'r', encoding='utf-8') as file:
        content = file.read()

    nlp = spacy.load('en_core_sci_sm')git
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


def loadAnns(target_dir, ann_file):
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
        content = file.readlines()

    pmc = ann_file.split(".")[0]

    # get all terms
    terms_tsv = [line.strip().split('\t') for line in content if line.startswith('T')]

    terms_loc = [term[2].split(" ") for term in terms_tsv]
    terms_df = pd.DataFrame(terms_tsv, columns=['t_id', 'annos', 'text'])
    terms_df[['label','start', 'end']] = [loc.split(" ") for loc in terms_df['annos']]
    terms_df = terms_df.drop(columns=['annos'])

    stars = [line.strip().split('\t') for line in content if line.startswith('*')]
    # todo there is a bug, ['*', 'PartOf T8 T9 T10']
    if stars:
        stars_df = pd.DataFrame(stars, columns=['s_id', 's_details'])
        new_stars_df = pd.DataFrame(columns=['s_type', 'arg1', 'arg2'])
        for star_indx in range(len(stars_df)):
            if len(stars_df.loc[star_indx, 's_details'].split(" ")) == 3:
                new_stars_df.loc[len(new_stars_df)] = stars_df.loc[star_indx, 's_details'].split(" ")
        stars_df = new_stars_df



    # relationships
    rels = [line.strip().split('\t') for line in content if line.startswith('R')]
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

    rels_json = json.loads(rels_df.to_json(orient='records'))
    rels_json = deleteNullJson(rels_json)
    with open(os.path.join(target_dir, pmc + "_rels.json"), 'w', encoding='utf-8') as file1:
        json.dump(rels_json, file1)

    # two types of attributes, yes/no or pick one value.
    attrs = [line.strip().split('\t') for line in content if line.startswith('A')]
    attrs_df = pd.DataFrame(attrs, columns=['a_id', 'attrs'])
    for attr_indx in range(len(attrs_df)):
        if len(attrs_df.loc[attr_indx, 'attrs'].split(" ")) == 2:
            new_value = attrs_df.loc[attr_indx, 'attrs'] + " True"
            attrs_df.loc[attr_indx, 'attrs'] = new_value


    attrs_df[["attrType", 'term', 'attrValue']] = [attr.split(" ") for attr in attrs_df['attrs']]
    attrs_df = attrs_df.drop(columns=['attrs'])

    # events
    events = [line.strip().split('\t') for line in content if line.startswith('E')]
    event_terms = [re.findall(r":(T\d+)", event[1]) for event in events]
    # event themselves are also terms. need to exclude them from the actual terms
    event_termID = [term[0] for term in event_terms]
    event_memberID = [term[1:] for term in event_terms]

    event_json = []
    for idx in range(len(events)):
        event_dict = {"eventID": events[idx][0], "eventTermID": event_termID[idx], "members": event_memberID[idx]}
        event_json.append(event_dict)

    # match attrs to terms
    terms_df = terms_df.merge(attrs_df, left_on='t_id', right_on='term', how='left')
    terms_df = terms_df.merge(rels_df, left_on='t_id', right_on='arg1', how='left')

    # add surrounding text
    with open(os.path.join(target_dir,pmc + ".txt"), 'r', encoding='utf-8') as file:
        content = file.read()
    terms_df = getTextWindow(terms_df, content)

    # add sentence index
    sent_idx = getSentenceIndex(pmc, target_dir)
    terms_df = getTermSentence(terms_df, sent_idx)

    terms_df = terms_df.rename(columns={'t_id_x':'t_id','label_x':'label', 'text_x':'text', 'start_x':'start', 'end_x':'end'})
    terms_df = terms_df.rename(columns={'label_y':'arg_label', 'text_y':'arg_text', 'start_y':'arg_start', 'end_y':'arg_end'})
    terms_df = terms_df[~terms_df['t_id'].isin(event_termID)]
    terms_df.to_csv(os.path.join(target_dir, pmc + "_terms.csv"))

    terms_json = json.loads(terms_df.to_json(orient='records'))
    terms_json = deleteNullJson(terms_json)
    with open(os.path.join(target_dir, pmc + "_terms.json"), 'w', encoding='utf-8') as file:
        json.dump(terms_json, file, indent=4)

    # map relationships, attributes, terms to events
    all_events = []
    for event in event_json:
        details = []
        details_wID = []
        event_loc = []
        for member in event["members"]:
            # one member could show up multiple times in the terms_df, therefore pick the first one
            event_loc.append(int(terms_df[terms_df["t_id"] == member]["start"].iloc[0]))
            # member_details could have multiple rows
            member_details = json.loads(terms_df[terms_df["t_id"] == member][["text","label","rel_id","attrType", "start","a_id","attrValue","rel_type","arg2","arg2_label","arg2_text","arg2_start"]].to_json(orient="records"))
            # an event can also have only one member.
            # onet event can have multiple members. here we only count those that are between event members
                  # todo relationship between a member a non-member is not counted.
            for a_member in member_details:
                if a_member["arg2"]:
                    # for extracting connected terms.
                    if a_member["arg2"] in event["members"]:
                        # record the location, cause we also need to sort the event members by location
                        triple = {a_member["rel_id"]:{"loc":round((int(a_member["start"]) + int(a_member["arg2_start"]))/2),
                                                      "content": (a_member["text"], a_member["rel_type"], a_member["arg2_text"])}}
                        details.append(triple)
                        triple_wID = {a_member["rel_id"]:{
                                            "loc":round((int(a_member["start"]) + int(a_member["arg2_start"]))/2),
                                            "content": ([member, a_member["label"],a_member["text"]], a_member["rel_type"], [a_member["arg2"], a_member["arg2_label"], a_member["arg2_text"]])}
                                    }
                        details_wID.append(triple_wID)
                    else:
                        if len(event["members"]) == 1:
                            triple = {member:{"loc":a_member["start"],
                                                          "content": ("event", "hasMember", a_member["text"])}}
                            details.append(triple)
                            triple_wID = {member:{
                                                "loc":a_member["start"],
                                                "content": ("event", "hasMember", [member, a_member["label"], a_member["text"]])}
                                        }
                            details_wID.append(triple_wID)
            # attributes of event members
            if a_member["attrValue"] is not None:
                triple = {a_member["a_id"]:{"content":(a_member["text"], a_member["attrType"], a_member["attrValue"])}}
                triple_wID = ([member, a_member["label"],a_member["text"]], a_member["attrType"], a_member["attrValue"])
                details.append(triple)
                details_wID.append(triple_wID)
        event["event_loc"] = round(sum(event_loc) / len(event_loc), 2)
        event["details"] = details
        event["details_wID"] = details_wID
        all_events.append(event)
    json.dump(all_events, open(os.path.join(target_dir, pmc + "_events.json"), 'w', encoding='utf-8'), indent=4)

    ## get the ordering of events
    """event_rels = [rel for rel in rels_json if rel["arg1"].startswith("E") and rel["arg2"].startswith("E")]
    print(event_rels)
    # there could be multiple branches of relationships, this way it is a order.
    event_orders = []
    seq_rel = [rel for rel in event_rels if rel["rel_type"] == "isAfter"]
    print(seq_rel)
    for rel in seq_rel:
        before = rel["arg2"]
        after = rel["arg1"]
        if before and after not in event_ordering:
            event_ordering.append(before)
            event_ordering.append(after)
        else:
            if before in event_ordering:
                event_ordering.insert(event_ordering.index(before)-1, after)
            if after in event_ordering:
                event_ordering.insert(event_ordering.index(after) + 1, before)
        print(event_ordering)
        input()
"""

    # get the extraction status making sure all annotations are extracted.
    extraction_status = [0] * len(content)
    for line in range(len(content)):
        if content[line].startswith('T'):
            extraction_status[line] = "Terms"
        elif content[line].startswith('A'):
            extraction_status[line] = "Attributes"
        elif content[line].startswith('Eq'):
            extraction_status[line] = "stars"
        elif content[line].startswith('R'):
            extraction_status[line] = "Relationships"
        elif content[line].startswith('#'):
            extraction_status[line] = "Notes"
    for line in range(len(content)):
        if extraction_status[line] == 0:
            extraction_status[line] = "Not extracted"


    with open(os.path.join(target_dir, pmc + "_extraction_status.txt"), 'w', encoding='utf-8') as file:
        file.write(str(Counter(extraction_status))
        + "\n" + "not extracted: " + str([content[line] for line in range(len(content)) if extraction_status[line] == 0]))

    return terms_df, rels_df


def main():
    target_dir  = "data/corpus3/"
    sub_dirs = ["train", "dev", "test"]
    for sub_dir in sub_dirs:
        target_subdir = os.path.join(target_dir,sub_dir)
        ann_files = getAnnFiles(target_subdir)


        for ann_file in ann_files:
            print(ann_file)
            try:
                terms_df, rels_df = loadAnns(target_subdir, ann_file)
                getSentenceIndex(ann_file.split(".")[0], target_subdir)
            except:
                print(f"\033[91m error in \033[0m", ann_file)

if __name__ == "__main__":
    main()
