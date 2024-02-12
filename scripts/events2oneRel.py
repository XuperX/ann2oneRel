# convert event to oneRel input format.
# one rel import example:
# run this one after inspectAnns.py
"""
[{  "text": original sentence, prefer one sentence, but can be across sentences if needed.
    "triple_list": [
            "Arg1",
            "/arg1Parentlabel/arg1DetailedLabel/Relationship]
            "Arg2"]
}]
https://github.com/China-ChallengeHub/OneRel/tree/main/data/NYT

Note: here I don't care about events, but the raltionships between entities.
"""
import os
import json
import pprint
from inspectAnns import getAnnFiles

def extract_multiSents(text, substring1, substring2):
    start_index = text.find(substring1)
    end_index = text.find(substring2)

    if start_index == -1 or end_index == -1:
        return "One or both substrings not found"

    # Ensure start_index is the first occurrence and end_index is the second
    if start_index > end_index:
        start_index, end_index = end_index, start_index
        substring1, substring2 = substring2, substring1

    return text[start_index:end_index + len(substring2)]

def merge_terms_by_sent(tripe_by_terms):
    # the original triple file were arranged as one triple as a unique object. but for this model, we want to organise them by sentences.
    merged = {}
    for d in tripe_by_terms:
        text = d['text']
        triple_list = d['triple_list']
        if text in merged:
            merged[text]['triple_list'].extend(triple_list)
        else:
            merged[text] = {'text': text, 'triple_list': triple_list}

    for term in merged:
        merged[term]['triple_list'] = list(set(tuple(triple) for triple in merged[term]['triple_list']))

    return list(merged.values())

def merge2multiSent(multi_sent_triples, single_sent_triples):
    # if the triple is across sentences, we need to merge triples that belong to one single sentences to the multi-sentence triples.
    new_single_sent_triples = []

    for single_sent_triple in single_sent_triples:
        single_sent_text = single_sent_triple['text']
        for multi_sent_triple in multi_sent_triples:
            multi_sent_text = multi_sent_triple['text']
            if single_sent_text in multi_sent_text:
                new_values = [item for item in single_sent_triple['triple_list'] if
                              item not in multi_sent_triple['triple_list']]
                multi_sent_triple['triple_list'].extend(new_values)
                multi_sent_triple['triple_list'] = list(set(tuple(triple) for triple in multi_sent_triple['triple_list']))

            else:
                new_single_sent_triples.append(single_sent_triple)

    return multi_sent_triples, new_single_sent_triples

def extract_triples(terms, original_text):
    text = original_text
    # rule 1: if arg 1 and arg 2 in the same sentence just extract
    # rule 2: if arg 1 and arg 2 in different sentences, check the original txt file, take the section which contains both.
    # rule 2 leads makes two sentences represented twice, each with partial relationships. Therefore for things extracted using rule 2, we need to copy the ones in a solo sentence down to the combined sentences.

    rule1_counter = 0
    rule1_content = []
    rule2_counter = 0
    rule2_content = []

    total_triples = []
    for term in terms:
        if "rel_type" in term.keys() and len(term["rel_type"])>0:
            total_triples.append(term)

    terms = total_triples

    for arg1_idx in range(len(terms)):
        arg1 = terms[arg1_idx]
        for arg2_idx in range(len(terms)):
            arg2 = terms[arg2_idx]
            if "arg2" in arg1.keys():
                if arg1["arg2"] == arg2["t_id"]:
                # rule 1
                    try:
                        if arg1["sentence_text"] == arg2["sentence_text"]:
                            rule1_counter += 1
                            extracted = {"text": arg1["sentence_text"].strip(), "triple_list": [[arg1["text"].strip(),arg1["label"], arg1["rel_type"], arg2["text"].strip()]]}
                            rule1_content.append(extracted)
                    except:
                        # in pmc4201588 there is a bug, a term is CEL.File. but our sentence splitter recogise . as a new sentence. that results in no sentence_text extracted
                        print("-----------")
                        pprint.pprint(arg1)
                        print("....")
                        pprint.pprint(arg2)
                # rule 2
                    else:
                        sent = extract_multiSents(text, arg1["sentence_text"], arg2["sentence_text"])
                        rule2_counter += 1
                        extracted = {"text": sent.strip(), "triple_list": [[arg1["text"].strip(),arg1["label"],arg1["rel_type"], arg2["text"].strip()]]}
                        rule2_content.append(extracted)
    return rule1_counter, rule1_content, rule2_counter, rule2_content

def triple2oneRelSchema(extracted_objs):
    # convert the extracted triples to the oneRel schema
    # things to be matched: one rel between different text are dicts of dicts, oneRel tripes are list of lists, one real Relationships are /arg1_parent/arg1_detailed/rel_type/
    new_objs = []
    for one_sent in extracted_objs:
        one_obj = {}
        one_obj['text'] = one_sent['text']
        one_obj['triple_list'] = []
        for triple in one_sent['triple_list']:
            triple = list(triple)
            one_triple = []
            arg1 = triple[0]
            arg1_label = triple[1]
            if arg1_label == "Operation":
                arg1_label = "Action/operation"
            elif arg1_label == "Data":
                arg1_label = "Data/data"
            elif arg1_label.lower() in ["software","algorithm","othermeans","hardware", "database","library"]:
                arg1_label = "Means/"+arg1_label
            elif arg1_label.lower() in ["url","version","identifier","id"]:
                arg1_label = "Descriptor/"+arg1_label

            rel_type = triple[2]
            arg2 = triple[3]
            one_triple.append(arg1)
            one_triple.append(arg1_label+"/"+rel_type)
            one_triple.append(arg2)
            one_obj['triple_list'].append(one_triple)
        new_objs.append(one_obj)

    return new_objs

if __name__ == "__main__":
    target_dir = "../data/corpus_v3"
    for corpus_dir in [os.path.join(target_dir,'/train'), os.path.join(target_dir,'/dev'), os.path.join(target_dir,'/test')]:

        ann_files = [file for file in os.listdir(corpus_dir) if file.endswith("_terms.json")]
        # there are relationships that are across multiple sentences. ideally they should all extracted.
        # but having sentences that are too long would make introduce many terms that weren't annotated.
        # also if one sentence is too short, it is possible it is mapped to something longer inaccurately.
        # therefore we set a cutoff for the number of sentences that a relationship can span.
        multi_sent_cutoff = 4

        debug = True

        all_rel = []
        for ann_file in ann_files:
            print(ann_file)
            input_file = os.path.join(corpus_dir, ann_file.split("_")[0] + "_terms.json")
            with open(input_file) as infile:
                terms = json.load(infile)
            txt_file = os.path.join(corpus_dir, ann_file.split("_")[0] + ".txt")
            with open(txt_file) as infile:

                text = infile.read()

            rule1_counter, rule1_content, rule2_counter, rule2_content = extract_triples(terms, text)

            if rule2_counter == 0:
                agg_aggr = merge_terms_by_sent(rule1_content)
                # this is the final
            if rule2_counter != 0:
                # first remove sentences that are too long.
                valid_rule2_content = []
                invalid_rule2_content = []
                for rule2_match in rule2_content:
                    # here i wanted to specify two sentences max, but in my original code, some sentences contain linebreaks, especially when it is a title.
                    if rule2_match["text"].count("\n") <= multi_sent_cutoff:
                        valid_rule2_content.append(rule2_match)
                else:
                    invalid_rule2_content.append(rule2_match)
                rule2_aggr = merge_terms_by_sent(valid_rule2_content)
                if invalid_rule2_content:
                    print("there are " + str(len(invalid_rule2_content)) + " invalid rule 2 content")


                # then merge rule 1 and rule 2
                multi, single = merge2multiSent(valid_rule2_content, rule1_content)
                agg_aggr = merge_terms_by_sent(multi + single)

                agg_aggr_oneRel = triple2oneRelSchema(agg_aggr)



            with open(os.path.join(corpus_dir, ann_file.split("_")[0] + "_oneRel.json"), "w") as outfile:
                json.dump(agg_aggr_oneRel, outfile, indent=4)
            all_rel.extend(agg_aggr_oneRel)
        with open(os.path.join(corpus_dir, "all_pub.json"), "w") as outfile:
            json.dump(all_rel, outfile, indent=4)





