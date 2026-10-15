"""Run:  python make_hash.py   -> prints MANAGER_PASS_HASH to paste into .env"""
import getpass
from werkzeug.security import generate_password_hash
p1 = getpass.getpass("Choose manager password: ")
if p1 != getpass.getpass("Repeat password: "): raise SystemExit("Passwords do not match.")
print("\nMANAGER_PASS_HASH=" + generate_password_hash(p1))