"""inspect or partially read Delft3D tekal ASCII file.
A tekal file consist of consecutive blocks,
each of which contain the following 4 items

many: *-marked comment lines
   1:name line with name of data block
   1:size line with number of rows, number of columns, and optionally the reshape dimensions for the row
many: data lines

  +----------------
  | * any number of header lines 
  | * ...
  | * each starting with an asterix
  | BLOCKNAME01
  | nrows ncols <nx ny>
  | row 
  | ...
  | row n
  +----------------

Example:

>> import tekal as tek
>> import numpy as np
>> import matplotlib.pyplot as plt

>> D = tek.tekal(fname) # initialize
>> D.info(fname)        # get     file meta-data: all blocks
>> print D              # display file contents: all blocks

block:      nvar       npts (   nx x  ny) nhdr 'blockname'
    0: nvar=  11 npts=   10 (   10 x   1)   22 'WL01'
    1: nvar=  11 npts=   10 (    5 x   2)   21 'WL02'

>> print D.blocks[33].header                  # display contents of one block 
>> M = D.read(33)                             # load one block into memory
>> plt.pcolormesh(M[0,:,:],M[1,:,:],M[6,:,:]) # plot 2D map data
>> plt.show()
"""

__version__ = "$Revision: 12836 $"

#  Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2013 Deltares
#       Gerben J. de Boer
#
#       gerben.deboer@deltares.nl
#
#   This library is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this library.  If not, see <http://www.gnu.org/licenses/>.
#   --------------------------------------------------------------------
#
# This tool is part of <a href="http://www.OpenEarth.eu">OpenEarthTools</a>.
# OpenEarthTools is an online collaboration to share and manage data and
# programming tools in an open source, version controlled environment.
# Sign up to recieve regular updates of this function, and to contribute
# your own tools.

# $Id: tekal.py 12836 2016-08-04 19:14:22Z kaaij $
# $Date: 2016-08-04 21:14:22 +0200 (Thu, 04 Aug 2016) $
# $Author: kaaij $
# $Revision: 12836 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/OpenEarthTools/openearthtools/io/delft3d/tekal.py $
# $Keywords: $

class tekalblock:
  """tekal file data block class"""
  
  def __init__(self):
    self.header = []
    self.nhdr   = None 
    self.index  = None  
    self.name   = None 
    self.npts   = None   
    self.nvar   = None  
    self.nx     = None  
    self.ny     = None 
    self.data   = None 
    self.tell   = float(0)
    
  def __str__(self):
    """print meta-info of tekal data block"""     
    txt = "%5g: nvar=%4g npts=%5g (%5g x%4g) %4s '%s'\n" % (self.index,self.nvar,self.npts,self.nx,self.ny,self.nhdr,self.name)
    return txt
    
  def strheader(self):
    """print meta-info header"""
    txt = "%5s:      %4s      %5s (%5s x%4s) %4s '%s'\n" % ('block','nvar','npts','nx','ny','nhdr','blockname')
    return txt
     
  def info(self,fid,index):
    """get meta-info of tekal data block """

    # !!! where to start reading actual matrix incl size header for check !!!
    self.tell  = fid.tell()

    # pass and store comment block
    rec = fid.readline()
    if len(rec)==0:
      return None;
    n   = 0
    while rec[0]=='*':
      self.header.append(rec)
      rec = fid.readline()
      n   = n+1
      
    # pass tekal block header
    self.index = index
    self.name  = rec.split()[0]

    # !!! after block name some file have meta-data (delf3d fourier file), so include this in header !!!
    self.header.append(rec)    
    self.nhdr = len(self.header)

    # pass tekal block data header    
    rec       = fid.readline()
    n         = n+1   
    recsplit = rec.replace(',', ' ').split()
    self.npts = int(recsplit[0])
    self.nvar = int(recsplit[1])
    if len(recsplit)==2:
       self.nx   = self.npts
       self.ny   = 1
    else:
       self.nx   = int(recsplit[2]) # npts
       self.ny   = int(recsplit[3]) # 1
    
    # pass tekal block data
    for i in range(self.npts):
      rec = fid.readline()
      n   = n+1
    return self
    
  def load(self,fid):
    """load data from 1 block (specified by index)
    from an opened tekal file identifier into a 
    3D numpy array that contains all variables from that block
    The shape of the returned 3D array(nvar,nx,ny) is
    0:          tekal columns: variables (all ascii columns)
    1: reshaped tekal rows   : nx for 2D data, npts for 1D data (all ascii rows)
    2: reshaped tekal rows   : ny for 2D data,    1 for 1D data
    The tekalblock object 
    
    >> fid = open(filename)
    >> tb = tekalblock.info(fid,index)
    >> M = tb.load(fid)
    >> fid.close()
    """
    import numpy as np

    # pass comment block
    rec = fid.readline()
    while rec[0]=='*':
      rec = fid.readline()
    #print rec
    rec = fid.readline()
    recsplit = rec.replace(',',' ').split()
    npts = int(recsplit[0])
    
    # Adjusted because this script does not allow lines with properties anyway
    # nvar = int(rec.split()[1])
    nvar = 2 # int(rec.split()[1]) 
    self.nvar = nvar
    
    if len(recsplit)==2:
       nx   = npts
       ny   = 1
    else:
       nx   = int(recsplit[2]) # npts
       ny   = int(recsplit[3]) # 1    
    if not(self.npts == npts): print('error')
    # if not(self.nvar == nvar): print 'error'
    if not(self.nx   == nx  ): print('error')
    if not(self.ny   == ny  ): print('error')
    M = np.zeros([self.nvar,self.nx,self.ny])    
    
    # load data block
    for ix in range(self.nx):
        for iy in range(self.ny):
            rec        = fid.readline()
            values     = rec.replace(',',' ').split()
            if len(values) > nvar: # If an unused third column is exported: remove
                values = values[:nvar]
            M[:,ix,iy] = values
          
    self.data = M
    return M

  def check(self):
    """Check block has valid content """    
    assert self.header is not []
    assert self.nhdr is not None 
    assert self.name is not None 
    assert self.npts is not None   
    assert self.nvar is not None  
    assert self.nx is not None  
    assert self.ny is not None 
    assert self.data is not None 
    
  def copy(self):
    """Create copy of tekalblock"""
    copy = tekalblock()
    copy.header = self.header[:]
    copy.nhdr   = self.nhdr
    copy.name   = self.name
    copy.npts   = self.npts
    copy.nvar   = self.nvar
    copy.nx     = self.nx
    copy.ny     = self.ny
    copy.data   = self.data.copy()
    return copy    
    
    
class tekal:
  """tekal file class """
  def __init__(self,filename):
    self.filename  = filename
    self.blocks    = [] # list of tekalblocks

  def append(self,block):
    """append block to tekal structure"""
    block.check()
    self.blocks.append(block)
    # set index
    self.blocks[-1].index = len(self.blocks)-1
    
  def __str__(self):
    """print meta-info of tekal file"""    
    txt = self.blocks[0].strheader()
    for index in range(len(self.blocks)):
      txt = txt + str(self.blocks[index])
    return txt
      
  def info(self,filename):
    """get meta-info of tekal file """
    fid = open(self.filename, "r")
    index = 0
    while True:
      B = tekalblock()
      B.info(fid,index)
      if B.npts==None:
         return
      index = index + 1
      self.blocks.append(B)
    fid.close()
    
  def read(self,index):
    """load data from 1 block (specified by index)
    from an unopened tekal filename into a 
    3D numpy array that contains all variables from that block
    The shape of the returned 3D array(nvar,nx,ny) is
    0:          tekal columns: variables (all ascii columns)
    1: reshaped tekal rows   : nx for 2D data, npts for 1D data (all ascii rows)
    2: reshaped tekal rows   : ny for 2D data,    1 for 1D data
    
    >> M = tekal.read(filename,index)
    """
    fid = open(self.filename,"r")
    fid.seek(self.blocks[index].tell)
    M = self.blocks[index].load(fid)
    fid.close()
    return M    

  def write(self):
    """write data to file
    
    Example:
    import copy
    D = tek.tekal(polfile1)           # initialize
    D.info(polfile)                   # get     file meta-data: all blocks

    E = tek.tekal(polfile2)           # initialize tekal file structure
    P = tek.tekalblock()              # initialize tekal block
    for k in range(99,102):           # loop through indices
      D.read(k)                       # load data for index k
      P = copy.copy(D.blocks[k])                              
      P.name = '{:s}_{:03g}'.format(P.name,k)
      P.header[-1] = P.name + '\n'    # Not sure about the Delft3D fourier type files (please check)
      E.append(P)                     # append tekal block to tekal file structure 
    E.write()                         # write file 
    """
    fid = open(self.filename,"a",0)
    for index in range(len(self.blocks)):
      print(index)
      self.blocks[index].check()
      fid.write(''.join(self.blocks[index].header))
      print(''.join(self.blocks[index].header))
      if self.blocks[index].ny == 1: 
        fid.write('{:g} {:g}\n'.format(self.blocks[index].npts,self.blocks[index].nvar))
      else:          
        fid.write('{:g} {:g} {:g}\n'.format(self.blocks[index].npts,self.blocks[index].nvar,self.blocks[index].ny))
      for iy in range(self.blocks[index].ny):    
        for ix in range(self.blocks[index].nx):    
          fid.write(' '.join(['{:f}'.format(v) for v in self.blocks[index].data[:,ix,iy]]) + '\n')
    fid.close()


if __name__ == '__main__':
  filepath = r'../test/testdata/Eijsden.pli'

  D = tekal(filepath)  # initialize
  D.info(filepath)  # get file meta-data: all blocks
