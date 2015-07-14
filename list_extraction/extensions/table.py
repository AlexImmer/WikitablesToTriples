from bs4 import BeautifulSoup
import sparql
import itertools
from keyExtractor import extractKeyColumn

class Table:

    """This class abstracts tables in Wikipedia articles to provide additional extraction functionality."""

    def __init__(self, soup, title):
        self.soup = soup
        self.caption = soup.find('caption')
        self.head = soup.find('thead')
        self.body = soup.find('tbody')
        self.section = self._section()
        self.columnNames = [th.text for th in self.soup.findAll('tr')[0].findAll('th')]
        self.pageTitle = title
        self.rows = [tr.findAll('th') + tr.findAll('td') for tr in self.soup.findAll('tr') if tr.find('td')]

    def __repr__(self):
        if self.caption:
            return self.caption.text
        return "Unnamed table in section \'%s\'" % self.section

    def _section(self):
        """Try finding first header (h2) before table.
        If none found, use the article's title."""
        for sibling in self.soup.previous_siblings:
            if sibling.name == 'h2':
                return sibling.span.text

        for parent in self.soup.parents:
            if parent.has_attr('id') and parent['id'] == 'content':
                return parent.h1.text

    def peek(self, chars=400):
        return self.soup.prettify()[:chars]

    def asDictionary(self, text=False):
        columnDict = {}
        for i, c in enumerate(self.columnNames):
            columnDict[c] = [str(row[i]) if text else row[i] for row in self.rows]
        return columnDict

    @property
    def columns(self):
        columns = []
        for i, c in enumerate(self.columnNames):
            columns.append([row[i] for row in self.rows])
        return columns

    @property
    def key(self):
        key = extractKeyColumn(self.soup, self.pageTitle, self.caption, '')
        if key != None:
            # Key object has following params:
            # entries, unique(no duplicate content), rating, xPos, title
            # entityCount(number of cells with an entity),
            # multipleEntities(true if at least one cell contains 2 entities),
            key = key['xPos']
        return key

    def row(self, i):
        return self.rows[i]

    def column(self, key, content=False):
        i = key if type(key) is int else self.columnNames.index(key)
        return [sparql.cellContent(row[i]) if content else row[i] for row in self.rows]

    def skip(self):
        # Something's wrong with rows (TODO: find 'something')

        if not self.rows:
            return True

        # Skip tables with unequal row lengths
        if max([len(row) for row in self.rows]) != min([len(row) for row in self.rows]):
            return True

        if max([len(row) for row in self.rows]) != len(self.columnNames):
            return True

        return False

    def predicatesForColumns(self, subColumn, objColumn, relative=True):
        """Return all predicates with subColumn's cells as subjects and objColumn's cells as objects.
        Set 'relative' to True if you want relative occurances."""
        subData = self.column(subColumn)
        objData = self.column(objColumn)
        predicates = {}
        for i in range(0, len(subData)):
            subContent = sparql.cellContent(subData[i])
            objContent = sparql.cellContent(objData[i])

            if not (objContent and sparql.isResource(subContent)):
                continue

            for predicate in sparql.predicates(subContent, objContent):
                if predicate in predicates:
                    predicates[predicate] += 1
                else:
                    predicates[predicate] = 1

        if relative:
            for p in predicates:
                predicates[p] = round(predicates[p]/len(subData), 2)

        return predicates

    def predicatesForKeyColumn(self, relative=True):
        """Return all predicates with subColumn as subject and all other columns as possible objects
        Set 'relative' to True if you want relative occurances."""
        objPredicates = {}
        for obj in columns:
            if obj == subColumn:
                continue

            objPredicates[obj] = self.predicatesForColumns(self.key, obj, relative=True)

        return objPredicates


    def predicatesForAllColumns(self, relative=True, omit=False):
        """Return predicates between all permutations of columns.
        Set 'omit' to 'True' to leave out empty ones."""
        predicates = []
        for subColumn, objColumn in itertools.permutations(self.columnNames, 2):
            pred = self.predicatesForColumns(subColumn, objColumn, relative)
            if pred or not omit:
                predicates.append({
                    'subject': subColumn,
                    'object': objColumn,
                    'predicates': pred
                })
        return predicates

    # def populateRows(self):
    #     trs = [tr.findAll('td') for tr in self.soup.findAll('tr') if tr.find('td')]
    #     rowLength = len(max(trs, lambda tr: len(tr)))
    #     rows = [[None for cell in range(0, rowLength)] for tr in trs]
    #
    #     for row, tr in enumerate(trs):
    #         col = 0
    #         for td in tr:
    #             while not rows[row][col]: col += 1
    #             rows[row][col] = td
    #
    #     return rows