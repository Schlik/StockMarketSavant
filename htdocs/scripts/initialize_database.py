from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, StockList, IndustryList
import csv
import logging

logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

engine = create_engine( 'mysql://schlik_db:jizm69@localhost/stocks')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine )
session = DBSession()

file = open( '/home/schlik/data/stock_symbols.CSV', 'rt' )
reader = csv.reader( file )   

##############################
####  FIRST Clean out old :
##############################
for stock in  session.query(StockList).all():
   print "stock : %s deleted " % stock.stock_symbol 
   session.delete( stock )

for ind in  session.query(IndustryList).all():
   print "industry : %s deleted " % ind.sector_name
   session.delete( ind )
session.commit()

##############################
####  Now reupdate:
##############################
for row in reader:
    industry = IndustryList( sector_name = row[2] )
    session.merge(industry)
    session.commit()
file.seek(0)
     
#for ind in  session.query(IndustryList).all():
#:w
#    print "MARCHLIK - industry : %s created" % ind.sector_name


for row in reader:
    industry = session.query( IndustryList ).filter_by( sector_name=row[2] ).one()
    stock = StockList(  stock_symbol = row[0], company_name = row[1], sector = industry.sector_name )
    session.add( stock )
session.commit()

file.close()

print "Total stocks in database : %s" % session.query( StockList ).count()
