from pathlib import Path

from form16_parser.table import Table
import fitz
import pymupdf


class PDF:
    def __init__(self, filepath: str | Path) -> None:
        self._filepath = filepath
        self._doc = fitz.open(str(self._filepath))
        self._tables = None
        self._first_columns = None

    def clear(self):
        self._doc.close()

    @property
    def tables(self):
        if self._tables is None:
            tables = []
            first_table_columns = []
            for page in self._doc:
                if page.first_widget:
                    page.delete_widget(page.first_widget) # Remove: "Signature" box
                for pymu_table in page.find_tables().tables:
                    df = pymu_table.to_pandas().reset_index().T.reset_index().T
                    table = Table(df=df, page=page)
                    first_table_columns.append(table.first_table_column)
                    tables.append(table)
            self._tables = tables
            self._first_table_columns = first_table_columns
        return self._tables
    
    @tables.setter
    def tables(self, new_tables):
        self._tables = new_tables

    @property
    def first_table_columns(self):
        if self._tables is None:
            # Creating tables creates self._first_table_columns
            _ = self.tables
        return self._first_table_columns