import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from bs4 import BeautifulSoup
import json, csv
import wikitables as w
from wikitables import Table, Page
from helper import *

savePath = './testdata/%s.json'
with open('./TitlesShuffled.csv', 'r') as f:
    titles = csv.reader(f)
    count = 0

    for title, *_ in titles:
        path = savePath % title.replace('/', '\\')

        if os.path.isfile(path):
            print(title)
            continue

        try:
            page = w.Page(title)
            data = page.predicates(relative=True, omit=True)
        except Exception:
            continue
        else:
            with open(path, 'w') as f:
                print(page.title)
                json.dump(data, f, indent=4)