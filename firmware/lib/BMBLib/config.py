import json

config = None
with open('config.json', 'r') as fid:
    config = json.load(fid)