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
import argparse
from pprint import pprint
from ann2termJSON import getSentenceIndex
from print_color import print

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
def merge_terms_by_sent(triple_by_terms):
    # the original triple file were arranged as one triple as a unique object. but for this model, we want to organise them by sentences.
    merged = {}
    for d in triple_by_terms:
        text = d['text']
        triple_list = d['triple_list']
        if text in merged:
            merged[text]['triple_list'].extend(triple_list)
        else:
            merged[text] = {'text': text, 'triple_list': triple_list}
    for term in merged:
        merged[term]['triple_list'] = list(set(tuple(triple) for triple in merged[term]['triple_list']))
    return list(merged.values())

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
            # arg1 is not an isolated term
            if "arg2" in arg1.keys():
                if arg1["arg2"] == arg2["t_id"]:
                    try: #one of the files contains a . within the term label. therefore, it doesn't have sentence_text.
                        if arg1["sentence_text"] == arg2["sentence_text"]:
                            rule1_counter += 1
                            extracted = {"text": arg1["sentence_text"].strip(), "triple_list": [[arg1["text"].strip(),arg1["label"], arg1["rel_type"], arg2["text"].strip(), arg2["label"]]]}
                            rule1_content.append(extracted)
                        # rule 2
                        else:
                            sent = extract_multiSents(text, arg1["sentence_text"], arg2["sentence_text"])
                            rule2_counter += 1
                            extracted = {"text": sent.strip(), "triple_list": [[arg1["text"].strip(),arg1["label"],arg1["rel_type"], arg2["text"].strip(),arg2["label"]]]}
                            rule2_content.append(extracted)
                    except:
                        continue
    return rule1_counter, rule1_content, rule2_counter, rule2_content
def triple2oneRelSchema(extracted_objs,target_dir):
    # convert the extracted triples to the oneRel schema
    # things to be matched: one rel between different text are dicts of dicts, oneRel tripes are list of lists, one real Relationships are /arg1_parent/arg1_detailed/rel_type/
    new_objs = []
    for one_sent in extracted_objs:
        if len(one_sent["triple_list"]) <= 0:
            new_objs.append(one_sent)
        else:
            one_obj = {}
            one_obj['text'] = one_sent['text']
            one_obj['triple_list'] = []
            with open(os.path.join(target_dir,"term2tripleRel.json"), "r") as f:
                term2triples = json.load(f)
                for triple in one_sent['triple_list']:
                    triple = list(triple)
                    one_triple = []
                    arg1 = triple[0]
                    arg1_label = triple[1]
                    for key, value in term2triples.items():
                        if arg1_label == key:
                            arg1_label = value

                    rel_type = triple[2]
                    arg2 = triple[3]
                    arg2_label = triple[4]
                    for key, value in term2triples.items():
                        if arg2_label == key:
                            arg2_label = value
                    one_triple.append(arg1)
                    one_triple.append(arg1_label+"/"+rel_type+"/"+arg2_label)
                    one_triple.append(arg2)
                    one_obj['triple_list'].append(one_triple)
            new_objs.append(one_obj)
    return new_objs
def inclEmptySents(triples_dic, sentences):
    existing_texts = [item['text'] for item in triples_dic]
    for sentence in sentences:
        if sentence['text'].strip() not in existing_texts:
            triples_dic.append({"text": sentence['text'].strip(), "triple_list": [""]})
            existing_texts.append(sentence['text'].strip())
            continue
    return triples_dic

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, default="data/corpus3")
    parser.add_argument("--withEmptySents", type=bool, default=True)
    args = parser.parse_args()
    target_dir = args.target_dir

    for corpus_dir in [os.path.join(target_dir,'train'), os.path.join(target_dir,'dev'), os.path.join(target_dir,'test')]:
        all_dir_data = []
        ann_files = [file for file in os.listdir(corpus_dir) if file.endswith("_terms.json")]
        # there are relationships that are across multiple sentences. ideally they should all extracted.
        # but having sentences that are too long would make introduce many terms that weren't annotated.
        # also if one sentence is too short, it is possible it is mapped to something longer inaccurately.
        # therefore we set a cutoff for the number of sentences that a relationship can span.
        multi_sent_cutoff = 4
        debug = True
        all_rel = []
        total_triple_count = 0
        for ann_file in ann_files:
            print(ann_file)
            input_file = os.path.join(corpus_dir, ann_file.split("_")[0] + "_terms.json")
            with open(input_file) as infile:
                terms = json.load(infile)
            txt_file = os.path.join(corpus_dir, ann_file.split("_")[0] + ".txt")
            with open(txt_file) as infile:
                text = infile.read()
            rule1_counter, rule1_content, rule2_counter, rule2_content = extract_triples(terms, text)
            # at this stage, one sentences could be represented in different objects if it contains more than one triple/
            sents = getSentenceIndex(ann_file.split("_")[0], corpus_dir)
            print("totel number of sentences: ", len(sents), color="green")
            rule1_content = inclEmptySents(rule1_content, sents) # if there are not triples, it has to be rule 1. note here the order has been shuffled.
            # if we don't consider triples that are generated across multiple sentences.
            all_singles = merge_terms_by_sent(rule1_content)
            all_content = all_singles


            if rule2_counter != 0:
                # first remove sentences that are too long.
                valid_rule2_content = []
                invalid_rule2_content = []
                for rule2_match in rule2_content:
                    if rule2_match["text"].count("\n") <= multi_sent_cutoff:
                        valid_rule2_content.append(rule2_match)
                    else:
                        invalid_rule2_content.append(rule2_match)
                rule2_aggr = merge_terms_by_sent(valid_rule2_content)

                if invalid_rule2_content:
                    print(str(len(invalid_rule2_content)) + " pair of terms that are in sentences far apart. They are discarded.")

            # joining the single sentences and multiple sentences.

                added_content = []
                for single_sent_tri in all_singles:
                    single_text = single_sent_tri['text']
                    inMulti=False
                    for multi_sent_tri in rule2_aggr:
                        if single_text in multi_sent_tri['text']:
                            multi_sent_tri['triple_list'].extend(single_sent_tri['triple_list'])
                            inMulti=True
                            break
                    if not inMulti:
                        added_content.append(single_sent_tri)
                added_content.extend(rule2_aggr)
                all_content = added_content

            # remove duplicated triples
            for content in all_content:
                unique_triples = list(set(content['triple_list']))
                unique_triples = [triple for triple in unique_triples if len(triple) > 0]
                content['triple_list'] = unique_triples
            # remove duplicated sentences:
            unique_sents = []
            unique_all_content = []
            for content in all_content:
                if content['text'] not in unique_sents:
                    unique_sents.append(content['text'])
                    unique_all_content.append(content)
                else:
                    all_triple = content['triple_list']
                    for existing_content in unique_all_content:
                        if existing_content['text'] == content['text']:
                            existing_content["triple_list"].extend(content['triple_list'])
                            existing_content["triple_list"] = list(set(existing_content["triple_list"]))
                            existing_content["triple_list"] = [triple for triple in existing_content["triple_list"] if len(triple) > 0]
                            break
            unique_all_content = [content for content in unique_all_content if len(content['text']) > 0]

            final_obj = triple2oneRelSchema(unique_all_content,target_dir)
            # represent empty ones using ""
            new_objs = []
            for obj in final_obj:
                if len(obj['triple_list']) == 0:
                    obj['triple_list'].append("")
                new_objs.append(obj)
            final_obj = new_objs

            with open(os.path.join(corpus_dir, ann_file.split("_")[0] + "_triples.json"), "w") as outfile:
                json.dump(final_obj, outfile, indent=4)
            all_dir_data.extend(final_obj)
        with open(os.path.join(corpus_dir, "all_triples.json"), "w") as outfile:
            json.dump(all_dir_data, outfile, indent=4)



