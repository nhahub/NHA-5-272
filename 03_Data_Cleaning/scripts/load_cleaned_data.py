"""Read-only loader for the cleaned v1.0.0 CSVs, for use by later project stages.

    import sys
    sys.path.insert(0, "03_Data_Cleaning/scripts")
    from load_cleaned_data import load_table, load_all
    orders = load_table("Sales_Orders")             # typed, hash-checked
    raw_text = load_table("Sales_Orders", typed=False)

Typed loading follows cleaning_schema.json (summarized in reports/Cleaned_CSV_Loading_Schema.csv):
IDs/LastEditedBy/barcodes/text -> string, integer measures -> Int64, bits -> boolean,
decimals -> Python Decimal (object), dates/timestamps -> datetime64[ns]. Only the literal
\\N is NULL. It never runs cleaning, never writes files and never coerces bad values to NULL.
"""
import json

from cleaning_pipeline import HERE, CLEANED, REPORTS, VERSION, convert_column, read_csv, require, sha256


def load_schema():
    return json.loads((HERE / "cleaning_schema.json").read_text(encoding="utf-8"))["datasets"]


def expected_hashes():
    manifest = json.loads((REPORTS / "source_to_output_manifest.json").read_text(encoding="utf-8"))
    return {item["dataset"]: item["output_sha256"] for item in manifest}


def load_table(name, typed=True, verify_hash=True, schema=None, hashes=None):
    schema = schema or load_schema()
    require(name in schema, f"Unknown dataset: {name}")
    spec, path = schema[name], CLEANED / VERSION / f"{name}.csv"
    if verify_hash:
        hashes = hashes or expected_hashes()
        require(sha256(path) == hashes[name], f"{name}: cleaned file differs from the v{VERSION} manifest")
    frame = read_csv(path)
    require(list(frame.columns) == [c["name"] for c in spec["columns"]], f"{name}: unexpected columns")
    require(len(frame) == spec["rows"], f"{name}: unexpected row count")
    if typed:
        for col in spec["columns"]:
            frame[col["name"]] = convert_column(frame[col["name"]], col)
    return frame


def load_all(typed=True, verify_hash=True):
    schema = load_schema()
    hashes = expected_hashes() if verify_hash else None
    return {name: load_table(name, typed, verify_hash, schema, hashes) for name in schema}
