from HTMLParser import HTMLParser
import urllib
import os

###### TO DO 
# ned to remove American International, Inc. - remove ","


# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    def __init__( self ):
        HTMLParser.__init__(self)
        self.stock_upcoming_token = False
        self.symbol_table_start = False
        self.table_column_count = 0
        self.current_column = 0
        self.stock_symbols = []
        self.get_stock_symbol_data = False
        self.completely_done = False
        
    def handle_starttag(self, tag, attrs):
        if tag == "table" and self.completely_done == False :
           self.symbol_table_start = True
           self.completely_done = True 
        if self.symbol_table_start and tag == "th":
            self.table_column_count += 1
        if tag == "td" and self.symbol_table_start:
           self.current_column += 1
        if self.current_column == 1:
           self.get_stock_symbol_data = True
        if self.current_column == 2:
           self.get_stock_symbol_data = True
        if self.current_column == 4:
           self.get_stock_symbol_data = True
        if self.current_column == self.table_column_count:
            self.current_column = 0

        #print "Encountered a start tag:", tag
    def handle_endtag(self, tag):
        if tag == "table":
           self.symbol_table_start = False
           #print "Encountered end tag for table:", tag
    def handle_data(self, data):
        if self.get_stock_symbol_data == True:
            self.get_stock_symbol_data = False
            #Remove comma
            data = data.replace(",","")
            self.stock_symbols.append( data )
            #print "Encountered some data  :", data
 
    def getSymbols(self, file):
        i = 0
        for stock in self.stock_symbols:
            i += 1
            if i % 3 == 0 :
               print file.write( stock + "\n" )
            else:
               print file.write( stock + "," )
 

# get the url to the list of S&P 500 Symbols
target_url = "http://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
filehandle = urllib.urlopen( target_url )

# instantiate the parser and fed it some HTML
parser = MyHTMLParser()
parser.feed( filehandle.read() )
file = open( '/home/schlik/data/stock_symbols.CSV', 'w' )
parser.getSymbols(file)
file.seek(-1, os.SEEK_END)
file.truncate()
file.close

           
