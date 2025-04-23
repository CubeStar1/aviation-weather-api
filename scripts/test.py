from MetaSum import Metasum
from PireSum import Piresum
from SigmetSum import Sigmetsum
from VFR import vfr
from path import path


full={"KLAX":10000,"KJFK":20000,"KPHX":1000}
IDs=list(full.keys())


Metarraw,Metarsum=Metasum(IDs)
print(Metarsum)

print()
Pirepraw,Pirepsum=Piresum(IDs)
print(Pirepsum)


print()
Sigmetraw,sigmetsum=Sigmetsum("10000")
print("There are a total of " + str(len(sigmetsum)) + " Sigmets Present")
for sigmet in sigmetsum:
    print(sigmet)

print()
pathraw,pathsum=path(IDs,Sigmetraw)

for brief in pathsum:
    print(brief)



print()
VFRdat=vfr(Metarraw,full)
print(VFRdat)

