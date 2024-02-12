
**TO RUN**
```
bash run.sh data/NCBI-disease
```

todo: the ncbi_disease set doesn't have term relationships, therefore it returns empty files. it only serves to demo the expected file structure.

## Data
**Required**
- train/
- test/
- dev/
- term2tripleRel.json
	The ann files usually preserve the most accurate annotations. but in the triple processing, we sometimes need to map it to other things. Therefore, please provide the original label and the final term label. 
	For example, 
	```sh
	# ann file
	T1 LabelX 34 48 Xtext
	T2 LabelY 54 69 Ytext
	R1 RelO	Arg1:T1 Arg2:T2

	# json file
	{"labelX":"TripleLabelX"}

	# final triple in the output
	{"TripleLabelX/RelO/TripleLabelY"}
	```

## Notes
1. sentence splitter
	Here I used the `en_core_sci_sm` model. It has some limitations when processing protein names with . in the middle or references.
	The key point is to make sure the sentences are split in the same way as the original .txt file. Therefore, I chose to continue using the en_core_sci_sm model

	here I used `en_core_sci_sm` within the scispacy package, which can be obtained from `https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz` 
2. **TODO sentences with no triples are not extracted**

## Known issues:
1. bug in the annotation configuration
	e.g. `* PartOf T8 T7 T9` 
	This is wrong because of the incorrect configuration in BRAT. such files are ignored in the fire.
2. some information in the ann files is not extracted. 
	Usually these are caused either by bugs in the configuration files, or just some annotations. They only contribute to 1/100 of the annotations therefore, we can ignore them.
3. in the ann2term file the debug function and the log function do not work together properly. but it is not causing big issues. 
4. using data/term2tripleRel.json 
	is largely a legacy thing. not very smart.
# todo 
1. improve the run.sh file. organise it properly using a json file
