> Note: this script wasn't originally designed for oneRel parsing. Therefore, there might be some redundancy in the data processing stages.
```mermaid
graph TB
	A[inspectAnn.py]
	B((

## Scripts:
- events2oneRel.py
	input: 
	- directories. (must include all data from the train, dev and development directories to ensure all types of relationships are extracted.
	- xx_terms.json: file that extracted all terms from the ann folder
## Data
	by default we 

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
