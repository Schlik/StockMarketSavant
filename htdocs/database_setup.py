############################
#####   END STOCK  #########
############################
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

############################
#####   END STOCK  #########
############################

############################
#####   CLASSES    #########
############################

class IndustryList(Base):
    __tablename__ = 'industry_list'
    sector_name = Column( String(50), nullable = False, primary_key = True)

#    @property 
#    def serialize(self):
#        return {
#            'sector_name'          : self.sector_name
#        }

class StockList(Base):
    __tablename__ = 'stock_list'
    id            = Column( Integer, primary_key = True )
    stock_symbol  = Column( String(50), nullable = False )
    company_name  = Column( String(100), nullable = False )
    sector        = Column( String(50), ForeignKey('industry_list.sector_name' ))
    industry_list = relationship( IndustryList )

#    @property 
#    def serialize(self):
#        return {
#            'id'          : self.id,
#            'symbol'      : self.stock_symbol,
#            'name'        : self.company_name,
#            'sector'      : self.sector
#        }

class User(Base):
    __tablename__ = 'user'
    id            = Column( Integer, primary_key = True )
    site_handle   = Column( String(250), nullable = False )
    email         = Column( String(250), nullable = False )
    #plus_id      = Column( Integer )
    #fb_id         = Column( Integer )
    #twitter_id    = Column( Integer )
    

#    @property 
#    def serialize(self):
#        return {
#            'name'        : self.name,
#            'picture'     : self.picture,
#            'email'       : self.email
    #        'gplus_id'    : self.gplus_id,
    #        'fb_id'       : self.fb_id,
    #        'twitter_id'  : self.twitter_id
#        }

class Portfolio(Base):
    __tablename__ = 'portfolio'
    id                     = Column( Integer, primary_key = True )
    energy_stock           = Column( Integer, ForeignKey('stock_list.id'))
#    financial_stock        = Column( Integer, ForeignKey('stock_list.id'))
#    it_stock               = Column( Integer, ForeignKey('stock_list.id'))
#    materials_stock        = Column( Integer, ForeignKey('stock_list.id'))
#    consumer_staples_stock = Column( Integer, ForeignKey('stock_list.id'))
    user_id                = Column( Integer, ForeignKey('user.id'))
    stock_list             = relationship( StockList )
    user                   = relationship( User )

#    @property 
#    def serialize(self):
#        return {
#            'energy'      : self.energy_stock,
#            'financial'   : self.financial_stock,
#            'tech'        : self.it_stock,
#            'materials'   : self.materials_stock,
#            'staple'      : self.consumer_staples_stock,
#            'user_id'     : self.user_id
#        }
    
############################
#insert at end of file :####
############################

engine = create_engine( 'mysql://schlik_db:jizm69@localhost/stocks')
Base.metadata.create_all(engine)
