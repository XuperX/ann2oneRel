> Note: this script wasn't originally designed for oneRel parsing. Therefore, there might be some redundancy in the data processing stages.


**TO RUN**
> bash run.sh data/NCBI-disease

todo: the ncbi_disease set doesn't have term relationships, therefore it returns empty files. it only serves to demo the expected file structure.

## Scripts:
- events2oneRel.py
	input: 
	- directories. (must include all data from the train, dev and development directories to ensure all types of relationships are extracted.
	- xx_terms.json: file that extracted all terms from the ann folder
## Data
	**Required**
	- train/
	- test/
	- dev/
	- term2tripleRel.json
		The ann files usually preserve the most accturate annotations. but in the triple processing we sometimes need to map it to other things. Therefore, please provide the original label and the final term label. 
		For example, if in ann file
		```
		# ann file
		T1 LabelX 34 48 Xtext
		T2 LabelY 54 69 Ytext
		R1 RelO	Arg1:T1 Arg2:T2
 		# json file
		{"labelX":"TripleLabelX"}
		# final triple in the output
		{"TripleLabelX/RelO/TripleLabelY"}
		```

## sentence splitter
	Here I used the `en_core_sci_sm` model. It has some limitations when it comes to process protein names with . in the middle or references.
	The key point is that to make sure the sentences are splitted in the same way as the original .txt file. There fore, I chose to continue using the en_core_sci_sm model

	here I used `en_core_sci_sm` within the scispacy package, which can be obtained from `https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz` 
	todo: add this to the yml file

## Dependency issues
1. pandas's compatibality with python3.8
	> python3.8 -m pip install --no-use-pep517 pandas
2. spacy package `en_core_sci_sm`
	> pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz

## Known issues:
1. bug in the annotation configuration
	e.g. `* PartOf T8 T7 T9` 
	This is wrong because of incorrect configuration in BRAT. such files are ignored in the fire.
2. some information in the ann files are not extracted. 
	Usually these are caused either by bugs in the configuration files, or just some annotations. They only contribute to 1/100 of the annotations therefore, we can ignore them.
3. in the inspectJson file the debug function and the log function do not work together properly. but it is not causing big issues. 
4. using data/term2tripleRel.json 
	is largely a legecy thing. not very smart.
# todo 
1. the log files of terms2oneRel.py is not there 
2. improve the run.sh file. organise it properly using a json file
3. empty sentences are not considered.
