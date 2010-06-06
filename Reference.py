import os, struct, common, archive

behaviourset = set()
behaviourlist = []

o0 = set()
o1 = set()
o2 = set()
o3 = set()
o4 = set()
o5 = set()
o6 = set()
o7 = set()

for file in os.listdir('/Users/Tempus/Downloads/New Super Mario Bros. Wii PAL/NSMB-Clean/Stage/Texture'):
    f = open('/Users/Tempus/Downloads/New Super Mario Bros. Wii PAL/NSMB-Clean/Stage/Texture/' + file, 'rb')
    data = f.read()
    f.close()

    name = file[:-4]
    
    arc = archive.U8()
    arc._load(data)
    

    # Load Objects
    objstrings = arc['BG_unt/{0}.bin'.format(name)]
    metadata = arc['BG_unt/{0}_hd.bin'.format(name)]
    
    meta = []
    for i in xrange(len(metadata)/4):
        meta.append(struct.unpack_from('>H2B', metadata, i * 4))                                    
        
    tilelist = [[]]
    upperslope = [0, 0]
    lowerslope = [0, 0]
    byte = 0
    print name
    for entry in meta:  
        offset = entry[0]
        byte = struct.unpack_from('>B', objstrings, offset)[0]
        row = 0
        
        while byte != 0xFF:

            if byte == 0xFE:
                tilelist.append([])

                if (upperslope[0] != 0) and (lowerslope[0] == 0):
                    upperslope[1] = upperslope[1] + 1
                    
                if lowerslope[0] != 0:
                    lowerslope[1] = lowerslope[1] + 1

                offset += 1
                byte = struct.unpack_from('>B', objstrings, offset)[0]

            elif (byte & 0x80):

                if upperslope[0] == 0:
                    upperslope[0] = byte
                else:
                    lowerslope[0] = byte
                
                offset += 1
                byte = struct.unpack_from('>B', objstrings, offset)[0]
                
            else:
                tilelist[len(tilelist)-1].append(struct.unpack_from('>3B', objstrings, offset))

                offset += 3
                byte = struct.unpack_from('>B', objstrings, offset)[0]

        tilelist.pop()

        if (upperslope[0] & 0x80) and (upperslope[0] & 0x2):
            for i in range(lowerslope[1]):
                pop = tilelist.pop()
                tilelist.insert(0, pop)
                
        o0.add(upperslope[0])
        o1.add(lowerslope[0])
        
        for tile in tilelist:
            for newtile in tile:
                print (newtile[2] & 0x3)
                o2.add(newtile[0])
                o3.add(newtile[2])
            
            
        tilelist = [[]]
        upperslope = [0, 0]
        lowerslope = [0, 0]



print 'Upperslope:'
for thing in o0:
    print hex(thing)
print '\n\n'

print 'Lowerslope:'
for thing in o1:
    print hex(thing)
print '\n\n'

print 'First Byte:'
for thing in o2:
    print hex(thing)
print '\n\n'


print 'Last Byte:'
for thing in o3:
    print hex(thing)
print '\n\n'


