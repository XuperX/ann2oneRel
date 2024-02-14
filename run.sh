target_dir="$1" wEmptySents="$2"
python scripts/ann2termJSON.py --target_dir=$target_dir
python scripts/terms2oneRel.py --target_dir=$target_dir --withEmptySents=wEmptySents
python scripts/oneRel_rel2id.py --target_dir=$target_dir
