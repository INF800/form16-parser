import pandas as pd

class Table:
    def __init__(self, df, page):
        self.page = page
        self.dataframe = df

    @property
    def page(self):
        return self._page
    
    @page.setter
    def page(self, new_page):
        self._page = new_page

    @property
    def page_number(self):
        if not self.page:
            return -1
        return self.page.number
        
    @property
    def dataframe(self):
        return self._dataframe
    
    @dataframe.setter
    def dataframe(self, new_dataframe):
        if isinstance(new_dataframe, pd.DataFrame):
            self._dataframe = new_dataframe
        else:
            raise ValueError("Data must be a pandas DataFrame")
    
    @property
    def first_table_cell(self):
        # Note: self.dataframe.iloc[0][0] contains index
        return self.dataframe.iloc[0][1]
    
    @property
    def first_table_column(self):
        return self.dataframe.iloc[:,1].to_list()
    
    @property
    def first_table_row(self):
        return self.dataframe.iloc[0, :].to_list()