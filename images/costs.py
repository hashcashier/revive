from __future__ import division
import matplotlib
matplotlib.rcParams['text.usetex'] = True
import matplotlib.pyplot as plt 
import matplotlib.lines as mlines
import numpy as np
import seaborn
seaborn.set(font_scale=2.3)
seaborn.set_style("whitegrid")
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import json
from pprint import pprint


width = 4
font = {'family' : 'normal',
	'weight' : 'normal',
	'size'   : 22}
plt.rc('font', **font)


with open('dframe.json') as data_file:    
    data = json.load(data_file)

pprint(data)

_x =[]
_y1=[]
_y2=[]

lines = ["-","--","--","-","-","-."]
for i in range(6):
    x = []
    y = []
    for j in range(24):
        x.append(data["x"][i*24+j])
        print data["x"][i*24+j]
        print data["y"][i*24+j]
        y.append(data["y"][i*24+j])
        if i == 1:
            _x.append(data["x"][i*24+j])
            _y1.append(data["y"][i*24+j])
        if i == 2:
            _y2.append(data["y"][i*24+j])
            
    plt.plot(x,y, lines[i], label=data["type"][i*24])
    print ""
    print data["type"][i*24]
    print ""

plt.fill_between(_x, _y1, _y2, color='green', alpha='0.2')

plt.xlabel("Number of Payment Channels")
plt.ylabel("Gas Costs (in 1000)")
#plt.title("From block height 360000 (June 2015)")
#plt.ylim(ymin=0)
#plt.legend(['True Positive Ratio'], loc='lower right')
#plt.legend(loc='upper center', prop={'size':20})
#plt.xlim(xlim=0)
plt.legend(prop={'size':16})
#plt.grid()
#host.grid(axis="y")
#plt.grid(axis='x')
fig = plt.gcf()
fig.tight_layout()
fig.set_size_inches(10,7)
plt.savefig("costs.pdf")
#plt.show()

