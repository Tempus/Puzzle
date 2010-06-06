#!/usr/bin/env python

import archive
import lz77
import os.path
import struct
import sys

from ctypes import create_string_buffer
from PyQt4 import QtCore, QtGui


try:
    import nsmblib
    HaveNSMBLib = True
except ImportError:
    HaveNSMBLib = False


########################################################
# To Do:
#
#   - Object Editor
#       - Adding/Removing Objects
#       - Moving the subblock around
#
#   - Fix UI a little
#   - More Icons
#   - C speed saving
#
########################################################


Tileset = None

#############################################################################################
########################## Tileset Class and Tile/Object Subclasses #########################

class TilesetClass():
    '''Contains Tileset data. Inits itself to a blank tileset.
    Methods: addTile, removeTile, addObject, removeObject, clear'''

    class Tile():
        def __init__(self, image, noalpha, bytelist):
            '''Tile Constructor'''
                        
            self.image = image
            self.noalpha = noalpha
            self.byte0 = bytelist[0]
            self.byte1 = bytelist[1]
            self.byte2 = bytelist[2]
            self.byte3 = bytelist[3]
            self.byte4 = bytelist[4]
            self.byte5 = bytelist[5]
            self.byte6 = bytelist[6]
            self.byte7 = bytelist[7]


    class Object():
    
        def __init__(self, height, width, uslope, lslope, tilelist):
            '''Tile Constructor'''
            
            self.height = height
            self.width = width
            
            self.upperslope = uslope
            self.lowerslope = lslope
            
            self.tiles = tilelist
                        

    def __init__(self):
        '''Constructor'''
        
        self.tiles = []
        self.objects = []
        
        self.slot = 0


    def addTile(self, image, noalpha, bytelist = (0, 0, 0, 0, 0, 0, 0, 0)):
        '''Adds an tile class to the tile list with the passed image or parameters'''

        self.tiles.append(self.Tile(image, noalpha, bytelist))
        

    def addObject(self, height = 1, width = 1,  uslope = [0, 0], lslope = [0, 0], tilelist = [[(0, 0, 0)]]):
        '''Adds a new object'''
        
        global Tileset
        
        if tilelist == [[(0, 0, 0)]]:
            tilelist = [[(0, 0, Tileset.slot)]]
            
        self.objects.append(self.Object(height, width, uslope, lslope, tilelist))
        
        
    def removeObject(self, index):
        '''Removes an Object by Index number. Don't use this much, because we want objects to preserve their ID.'''
        
        self.objects.pop(index)
       
    
    def clear(self):
        '''Clears the tileset for a new file'''
        
        self.tiles = []
        self.objects = []
        
        
    def clearObjects(self):
        '''Clears the object data'''
        
        self.objects = []
        
        
    def clearCollisions(self):
        '''Clears the collisions data'''
        
        for tile in self.tiles:
            tile.byte0 = 0
            tile.byte1 = 0
            tile.byte2 = 0
            tile.byte3 = 0
            tile.byte4 = 0
            tile.byte5 = 0
            tile.byte6 = 0
            tile.byte7 = 0


#############################################################################################
######################### Palette for painting behaviours to tiles ##########################


class paletteWidget(QtGui.QWidget):
    
    def __init__(self, window):
        super(paletteWidget, self).__init__(window)


        # Core Types Radio Buttons and Tooltips
        self.coreType = QtGui.QGroupBox()
        self.coreType.setTitle('Core Type:')
        self.coreWidgets = []
        coreLayout = QtGui.QVBoxLayout()
        rowA = QtGui.QHBoxLayout()
        rowB = QtGui.QHBoxLayout()
        rowC = QtGui.QHBoxLayout()
        rowD = QtGui.QHBoxLayout()
        rowE = QtGui.QHBoxLayout()
        rowF = QtGui.QHBoxLayout()

        path = os.path.dirname(os.path.abspath(sys.argv[0])) + '/Icons/'
        
        self.coreTypes = [['Default', QtGui.QIcon(path + 'Core/Default.png'), 'The standard type for tiles.\n\nAny regular terrain or backgrounds\nshould be of generic type. It\n has no collision properties.'], 
                     ['Slope', QtGui.QIcon(path + 'Core/Slope.png'), 'Defines a sloped tile\n\nSloped tiles have sloped collisions,\nwhich Mario can slide on.'], 
                     ['Reverse Slope', QtGui.QIcon(path + 'Core/RSlope.png'), 'Defines an upside-down slope.\n\nSloped tiles have sloped collisions,\nwhich Mario can slide on.'], 
                     ['Partial Block', QtGui.QIcon(path + 'Partial/Full.png'), 'Used for blocks with partial collisions.\n\nVery useful for Mini-Mario secret\nareas, but also for providing a more\naccurate collision map for your tiles.'],
                     ['Coin', QtGui.QIcon(path + 'Core/Coin.png'), 'Creates a coin.\n\nCoins have no solid collision,\nand when touched will disappear\nand increment the coin counter.'], 
                     ['Explodable Block', QtGui.QIcon(path + 'Core/Explode.png'), 'Specifies blocks which can explode.\n\nThese blocks will shatter into componenent\npieces when hit by a bom-omb or meteor.\nThe pieces themselves may be hardcoded\nand must be included in the tileset.\nBehaviour may be sporadic.'], 
                     ['Climable Grid', QtGui.QIcon(path + 'Core/Climb.png'), 'Creates terrain that can be climbed on.\n\nClimable terrain cannot be walked on.\nWhen Mario is overtop of a climable\ntile and the player presses up,\nMario will enter a climbing state.'], 
                     ['Spike', QtGui.QIcon(path + 'Core/Spike.png'), 'Dangerous Spikey spikes.\n\nSpike tiles will damage Mario one hit\nwhen they are touched.'], 
                     ['Pipe', QtGui.QIcon(path + 'Core/Pipe.png'), "Denotes a pipe tile.\n\nPipe tiles are specified according to\nthe part of the pipe. It's important\nto specify the right parts or\nentrances will not function correctly."], 
                     ['Rails', QtGui.QIcon(path + 'Core/Rails.png'), 'Used for all types of rails.\n\nRails are replaced in-game with\n3D models, so modifying these\ntiles with different graphics\nwill have no effect.'], 
                     ['Conveyor Belt', QtGui.QIcon(path + 'Core/Conveyor.png'), 'Defines moving tiles.\n\nMoving tiles will move Mario in one\ndirection or another. Parameters are\nlargely unknown at this time.']]

        i = 0
        for item in range(len(self.coreTypes)):
            self.coreWidgets.append(QtGui.QRadioButton())
            if i == 0:
                self.coreWidgets[item].setText('Default')
            else:
                self.coreWidgets[item].setIcon(self.coreTypes[item][1])
            self.coreWidgets[item].setIconSize(QtCore.QSize(24, 24))
            self.coreWidgets[item].setToolTip(self.coreTypes[item][2])
            self.coreWidgets[item].clicked.connect(self.swapParams)
            if i < 1:
                rowA.addWidget(self.coreWidgets[item])
            elif i < 3:
                rowB.addWidget(self.coreWidgets[item])
            elif i < 5:
                rowC.addWidget(self.coreWidgets[item])
            elif i < 7:
                rowD.addWidget(self.coreWidgets[item])
            elif i < 9:
                rowE.addWidget(self.coreWidgets[item])
            else:
                rowF.addWidget(self.coreWidgets[item])
            i += 1

        coreLayout.addLayout(rowA)
        coreLayout.addLayout(rowB)
        coreLayout.addLayout(rowC)
        coreLayout.addLayout(rowD)
        coreLayout.addLayout(rowE)
        coreLayout.addLayout(rowF)
        self.coreType.setLayout(coreLayout)


        # Properties Buttons. I hope this works well!
        self.propertyGroup = QtGui.QGroupBox()
        self.propertyGroup.setTitle('Properties:')
        propertyLayout = QtGui.QVBoxLayout()
        self.propertyWidgets = []
        propertyList = [['Solid', QtGui.QIcon(path + 'Prop/Solid.png'), 'Tiles you can walk on.\n\nThe tiles we be a solid basic square\nthrough which Mario can not pass.'], 
                        ['Block', QtGui.QIcon(path + 'Prop/Break.png'), 'This denotes breakable tiles such\nas brick blocks and Q blocks. It is likely that these\nare subject to the same issues as\nexplodable blocks. They emit a coin\nwhen hit.'],            
                        ['Falling Block', QtGui.QIcon(path + 'Prop/Fall.png'), 'Sets the block to fall after a set period. The\nblock is sadly replaced with a donut lift model\nfor all animations.'], 
                        ['Ledge', QtGui.QIcon(path + 'Prop/Ledge.png'), 'A ledge tile with unique properties.\n\nLedges can be shimmied along or\nhung from, but not walked along\nas with normal terrain. Must have the\nledge terrain type set as well.']]
        
        for item in range(len(propertyList)):
            self.propertyWidgets.append(QtGui.QCheckBox(propertyList[item][0]))
            self.propertyWidgets[item].setIcon(propertyList[item][1])
            self.propertyWidgets[item].setIconSize(QtCore.QSize(24, 24))
            self.propertyWidgets[item].setToolTip(propertyList[item][2])
            propertyLayout.addWidget(self.propertyWidgets[item])
        

        self.PassThrough = QtGui.QRadioButton('Pass-Through')
        self.PassDown = QtGui.QRadioButton('Pass-Down')
        self.PassNone = QtGui.QRadioButton('No Passing')

        self.PassThrough.setIcon(QtGui.QIcon(path + 'Prop/Pup.png'))
        self.PassDown.setIcon(QtGui.QIcon(path + 'Prop/Pdown.png'))
        self.PassNone.setIcon(QtGui.QIcon(path + 'Prop/Pnone.png'))

        self.PassThrough.setIconSize(QtCore.QSize(24, 24))
        self.PassDown.setIconSize(QtCore.QSize(24, 24))
        self.PassNone.setIconSize(QtCore.QSize(24, 24))

        self.PassThrough.setToolTip('Allows Mario to jump through the bottom\nof the tile and land on the top.')
        self.PassDown.setToolTip('Allows Mario to fall through the tile but\n be able to jump up through it. Originally\nused for invisible Q blocks.')
        self.PassNone.setToolTip('Default setting')

        propertyLayout.addWidget(self.PassNone)
        propertyLayout.addWidget(self.PassThrough)
        propertyLayout.addWidget(self.PassDown)

        self.propertyGroup.setLayout(propertyLayout)



        # Terrain Type ComboBox
        self.terrainType = QtGui.QComboBox()
        self.terrainLabel = QtGui.QLabel('Terrain Type')
 
        self.terrainTypes = [['Default', QtGui.QIcon(path + 'Core/Default.png')],
                        ['Ice', QtGui.QIcon(path + 'Terrain/Ice.png')], 
                        ['Snow', QtGui.QIcon(path + 'Terrain/Snow.png')], 
                        ['Quicksand', QtGui.QIcon(path + 'Terrain/Quicksand.png')], 
                        ['Conveyor Belt Right', QtGui.QIcon(path + 'Core/Conveyor.png')], 
                        ['Conveyor Belt Left', QtGui.QIcon(path + 'Core/Conveyor.png')],
                        ['Horiz. Climbing Rope', QtGui.QIcon(path + 'Terrain/Rope.png')], 
                        ['Damage Tile', QtGui.QIcon(path + 'Terrain/Spike.png')], 
                        ['Ledge', QtGui.QIcon(path + 'Terrain/Ledge.png')], 
                        ['Ladder', QtGui.QIcon(path + 'Terrain/Ladder.png')], 
                        ['Staircase', QtGui.QIcon(path + 'Terrain/Stairs.png')], 
                        ['Carpet', QtGui.QIcon(path + 'Terrain/Carpet.png')], 
                        ['Dusty', QtGui.QIcon(path + 'Terrain/Dust.png')], 
                        ['Grass', QtGui.QIcon(path + 'Terrain/Grass.png')], 
                        ['Muffled', QtGui.QIcon(path + 'Unknown.png')], 
                        ['Beach Sand', QtGui.QIcon(path + 'Terrain/Sand.png')]]

        for item in range(len(self.terrainTypes)):
            self.terrainType.addItem(self.terrainTypes[item][1], self.terrainTypes[item][0])
            self.terrainType.setIconSize(QtCore.QSize(24, 24))
        self.terrainType.setToolTip('Set the various types of terrain.\n\n'
                                    
                                    '<b>Default:</b> \nTerrain with no paticular properties.\n\n'
                                    '<b>Ice:</b> \nWill be slippery.\n\n'
                                    '<b>Snow:</b> \nWill emit puffs of snow and snow noises.\n\n'
                                    '<b>Quicksand:</b> \nWill slowly swallow Mario as if\nin quicksand. No animation.'
                                    '<b>Conveyor Belt Right:</b> \nMario moves slowly rightwards.'
                                    '<b>Converyor Belt Left:</b> \nMario moves slowly leftwards.'
                                    '<b>Horiz. Rope:</b> \nMust be solid to function.\nMario will move hand-over-hand\nalong the rope.'
                                    '<b>Damage Tile:</b> \nTile causes damage like a spike.'
                                    '<b>Ledge:</b> \nMust have ledge property set as well.'
                                    '<b>Ladder:</b> \nActs as a ladder. Mario will face right\nor left as he climbs.'
                                    '<b>Staricase:</b> \nSliding is not allowed on slopes, and\nhas other characteristics of a staircase.'
                                    '<b>Carpet:</b> \nWill muffle footstep noises.'
                                    '<b>Dusty:</b> \nWill emit puffs of dust.'
                                    '<b>Muffled:</b> \nMostly muffles footstep noises.'
                                    '<b>Grass:</b> \nWill emit grass-like footstep noises.'
                                    "<b>Beach Sand:</b> \nWill create sand tufts around\nMario's feet."
                                   )

        
        
        # Parameters ComboBox
        self.parameters = QtGui.QComboBox()
        self.parameterLabel = QtGui.QLabel('Parameters')
        self.parameters.addItem('None')

        
        GenericParams = [['None', QtGui.QIcon(path + 'Core/Default.png')],
                         ['Beanstalk Stop', QtGui.QIcon(path + '/Generic/Beanstopper.png')], 
                         ['Dash Coin', QtGui.QIcon(path + 'Generic/Outline.png')], 
                         ['Battle Coin', QtGui.QIcon(path + 'Generic/Outline.png')],
                         ['Red Block Outline A', QtGui.QIcon(path + 'Generic/RedBlock.png')], 
                         ['Red Block Outline B', QtGui.QIcon(path + 'Generic/RedBlock.png')], 
                         ['Cave Entrance Right', QtGui.QIcon(path + 'Generic/Cave-Right.png')], 
                         ['Cave Entrance Left', QtGui.QIcon(path + 'Generic/Cave-Left.png')], 
                         ['Unknown', QtGui.QIcon(path + 'Unknown.png')],
                         ['Unknown', QtGui.QIcon(path + 'Unknown.png')]]
        
        RailParams = [['None', QtGui.QIcon(path + 'Core/Default.png')],
                      ['Rail: Upslope', QtGui.QIcon(path + '')], 
                      ['Rail: Downslope', QtGui.QIcon(path + '')], 
                      ['Rail: 90 degree Corner Fill', QtGui.QIcon(path + '')], 
                      ['Rail: 90 degree Corner', QtGui.QIcon(path + '')], 
                      ['Rail: Horizontal Rail', QtGui.QIcon(path + '')], 
                      ['Rail: Vertical Rail', QtGui.QIcon(path + '')], 
                      ['Rail: Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Rail: Gentle Upslope 2', QtGui.QIcon(path + '')], 
                      ['Rail: Gentle Upslope 1', QtGui.QIcon(path + '')], 
                      ['Rail: Gentle Downslope 2', QtGui.QIcon(path + '')], 
                      ['Rail: Gentle Downslope 1', QtGui.QIcon(path + '')], 
                      ['Rail: Steep Upslope 2', QtGui.QIcon(path + '')], 
                      ['Rail: Steep Upslope 1', QtGui.QIcon(path + '')], 
                      ['Rail: Steep Downslope 2', QtGui.QIcon(path + '')], 
                      ['Rail: Steep Downslope 1', QtGui.QIcon(path + '')], 
                      ['Rail: One Panel Circle', QtGui.QIcon(path + '')], 
                      ['Rail: 2x2 Circle Upper Right', QtGui.QIcon(path + '')], 
                      ['Rail: 2x2 Circle Upper Left', QtGui.QIcon(path + '')], 
                      ['Rail: 2x2 Circle Lower Right', QtGui.QIcon(path + '')], 
                      ['Rail: 2x2 Circle Lower Left', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Top Left Corner', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Top Left', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Top Right', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Top Right Corner', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Upper Left Side', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Upper Right Side', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Lower Left Side', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Lower Right Side', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Bottom Left Corner', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Bottom Left', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Bottom Right', QtGui.QIcon(path + '')], 
                      ['Rail: 4x4 Circle Bottom Right Corner', QtGui.QIcon(path + '')], 
                      ['Rail: Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Rail: End Stop', QtGui.QIcon(path + '')]]
        
        ClimableGridParams = [['None', QtGui.QIcon(path + 'Core/Default.png')],
                             ['Free Move', QtGui.QIcon(path + 'Climb/Center.png')], 
                             ['Upper Left Corner', QtGui.QIcon(path + 'Climb/UpperLeft.png')], 
                             ['Top', QtGui.QIcon(path + 'Climb/Top.png')], 
                             ['Upper Right Corner', QtGui.QIcon(path + 'Climb/UpperRight.png')], 
                             ['Left Side', QtGui.QIcon(path + 'Climb/Left.png')], 
                             ['Center', QtGui.QIcon(path + 'Climb/Center.png')], 
                             ['Right Side', QtGui.QIcon(path + 'Climb/Right.png')], 
                             ['Lower Left Corner', QtGui.QIcon(path + 'Climb/LowerLeft.png')], 
                             ['Bottom', QtGui.QIcon(path + 'Climb/Bottom.png')], 
                             ['Lower Right Corner', QtGui.QIcon(path + 'Climb/LowerRight.png')]]
        
        
        CoinParams = [['Generic Coin', QtGui.QIcon(path + 'QBlock/Coin.png')],
                     ['Coin', QtGui.QIcon(path + 'Unknown.png')], 
                     ['Nothing', QtGui.QIcon(path + 'Unknown.png')],
                     ['Coin', QtGui.QIcon(path + 'Unknown.png')], 
                     ['Pow Block Coin', QtGui.QIcon(path + 'Coin/POW.png')]]
                 
        ExplodableBlockParams = [['None', QtGui.QIcon(path + 'Core/Default.png')],
                                ['Stone Block', QtGui.QIcon(path + 'Explode/Stone.png')], 
                                ['Wooden Block', QtGui.QIcon(path + 'Explode/Wooden.png')], 
                                ['Red Block', QtGui.QIcon(path + 'Explode/Red.png')], 
                                ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                                ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                                ['Unknown', QtGui.QIcon(path + 'Unknown.png')]]
        
        PipeParams = [['Vert. Top Entrance Left', QtGui.QIcon(path + 'Pipes/')], 
                      ['Vert. Top Entrance Right', QtGui.QIcon(path + '')], 
                      ['Vert. Bottom Entrance Left', QtGui.QIcon(path + '')], 
                      ['Vert. Bottom Entrance Right', QtGui.QIcon(path + '')], 
                      ['Vert. Center Left', QtGui.QIcon(path + '')], 
                      ['Vert. Center Right', QtGui.QIcon(path + '')], 
                      ['Vert. On Top Junction Left', QtGui.QIcon(path + '')], 
                      ['Vert. On Top Junction Right', QtGui.QIcon(path + '')], 
                      ['Horiz. Left Entrance Top', QtGui.QIcon(path + '')], 
                      ['Horiz. Left Entrance Bottom', QtGui.QIcon(path + '')], 
                      ['Horiz. Right Entrance Top', QtGui.QIcon(path + '')], 
                      ['Horiz. Right Entrance Bottom', QtGui.QIcon(path + '')], 
                      ['Horiz. Center Left', QtGui.QIcon(path + '')], 
                      ['Horiz. Center Right', QtGui.QIcon(path + '')], 
                      ['Horiz. On Top Junction Top', QtGui.QIcon(path + '')], 
                      ['Horiz. On Top Junction Bottom', QtGui.QIcon(path + '')], 
                      ['Vert. Mini Pipe Top', QtGui.QIcon(path + '')], 
                      ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Vert. Mini Pipe Bottom', QtGui.QIcon(path + '')], 
                      ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Vert. On Top Mini-Junction', QtGui.QIcon(path + '')], 
                      ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Horiz. Mini Pipe Left', QtGui.QIcon(path + '')], 
                      ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Horiz. Mini Pipe Right', QtGui.QIcon(path + '')], 
                      ['Unknown', QtGui.QIcon(path + 'Unknown.png')], 
                      ['Vert. Mini Pipe Center', QtGui.QIcon(path + '')], 
                      ['Horiz. Mini Pipe Center', QtGui.QIcon(path + '')], 
                      ['Horiz. On Top Mini-Junction', QtGui.QIcon(path + '')], 
                      ['Block Covered Corner', QtGui.QIcon(path + '')]]
                                       
        PartialBlockParams = [['None', QtGui.QIcon(path + 'Core/Default.png')],
                              ['Upper Left', QtGui.QIcon(path + 'Partial/UpLeft.png')], 
                              ['Upper Right', QtGui.QIcon(path + 'Partial/UpRight.png')], 
                              ['Top Half', QtGui.QIcon(path + 'Partial/TopHalf.png')], 
                              ['Lower Left', QtGui.QIcon(path + 'Partial/LowLeft.png')], 
                              ['Left Half', QtGui.QIcon(path + 'Partial/LeftHalf.png')], 
                              ['Diagonal Downwards', QtGui.QIcon(path + 'Partial/DiagDn.png')], 
                              ['Upper Left 3/4', QtGui.QIcon(path + 'Partial/UpLeft3-4.png')], 
                              ['Lower Right', QtGui.QIcon(path + 'Partial/LowRight.png')], 
                              ['Diagonal Downwards', QtGui.QIcon(path + 'Partial/DiagDn.png')], 
                              ['Right Half', QtGui.QIcon(path + 'Partial/RightHalf.png')], 
                              ['Upper Right 3/4', QtGui.QIcon(path + 'Partial/UpRig3-4.png')], 
                              ['Lower Half', QtGui.QIcon(path + 'Partial/LowHalf.png')], 
                              ['Lower Left 3/4', QtGui.QIcon(path + 'Partial/LowLeft3-4.png')], 
                              ['Lower Right 3/4', QtGui.QIcon(path + 'Partial/LowRight3-4.png')], 
                              ['Full Brick', QtGui.QIcon(path + 'Partial/Full.png')]]
        
        SlopeParams = [['Steep Upslope', QtGui.QIcon(path + 'Slope/steepslopeleft.png')], 
                       ['Steep Downslope', QtGui.QIcon(path + 'Slope/steepsloperight.png')], 
                       ['Upslope 1', QtGui.QIcon(path + 'Slope/slopeleft.png')], 
                       ['Upslope 2', QtGui.QIcon(path + 'Slope/slope3left.png')], 
                       ['Downslope 1', QtGui.QIcon(path + 'Slope/slope3right.png')], 
                       ['Downslope 2', QtGui.QIcon(path + 'Slope/sloperight.png')], 
                       ['Steep Upslope 1', QtGui.QIcon(path + 'Slope/vsteepup1.png')], 
                       ['Steep Upslope 2', QtGui.QIcon(path + 'Slope/vsteepup2.png')], 
                       ['Steep Downslope 1', QtGui.QIcon(path + 'Slope/vsteepdown1.png')], 
                       ['Steep Downslope 2', QtGui.QIcon(path + 'Slope/vsteepdown2.png')], 
                       ['Slope Edge (solid)', QtGui.QIcon(path + 'Slope/edge.png')], 
                       ['Gentle Upslope 1', QtGui.QIcon(path + 'Slope/gentleupslope1.png')], 
                       ['Gentle Upslope 2', QtGui.QIcon(path + 'Slope/gentleupslope2.png')], 
                       ['Gentle Upslope 3', QtGui.QIcon(path + 'Slope/gentleupslope3.png')], 
                       ['Gentle Upslope 4', QtGui.QIcon(path + 'Slope/gentleupslope4.png')], 
                       ['Gentle Downslope 1', QtGui.QIcon(path + 'Slope/gentledownslope1.png')], 
                       ['Gentle Downslope 2', QtGui.QIcon(path + 'Slope/gentledownslope2.png')], 
                       ['Gentle Downslope 3', QtGui.QIcon(path + 'Slope/gentledownslope3.png')], 
                       ['Gentle Downslope 4', QtGui.QIcon(path + 'Slope/gentledownslope4.png')]]
                       
        ReverseSlopeParams = [['Steep Downslope', QtGui.QIcon(path + 'Slope/Rsteepslopeleft.png')], 
                              ['Steep Upslope', QtGui.QIcon(path + 'Slope/Rsteepsloperight.png')], 
                              ['Downslope 1', QtGui.QIcon(path + 'Slope/Rslopeleft.png')], 
                              ['Downslope 2', QtGui.QIcon(path + 'Slope/Rslope3left.png')], 
                              ['Upslope 1', QtGui.QIcon(path + 'Slope/Rslope3right.png')], 
                              ['Upslope 2', QtGui.QIcon(path + 'Slope/Rsloperight.png')], 
                              ['Steep Downslope 1', QtGui.QIcon(path + 'Slope/Rvsteepdown1.png')], 
                              ['Steep Downslope 2', QtGui.QIcon(path + 'Slope/Rvsteepdown2.png')], 
                              ['Steep Upslope 1', QtGui.QIcon(path + 'Slope/Rvsteepup1.png')], 
                              ['Steep Upslope 2', QtGui.QIcon(path + 'Slope/Rvsteepup2.png')], 
                              ['Slope Edge (solid)', QtGui.QIcon(path + 'Slope/edge.png')], 
                              ['Gentle Downslope 1', QtGui.QIcon(path + 'Slope/Rgentledownslope1.png')], 
                              ['Gentle Downslope 2', QtGui.QIcon(path + 'Slope/Rgentledownslope2.png')], 
                              ['Gentle Downslope 3', QtGui.QIcon(path + 'Slope/Rgentledownslope3.png')], 
                              ['Gentle Downslope 4', QtGui.QIcon(path + 'Slope/Rgentledownslope4.png')], 
                              ['Gentle Upslope 1', QtGui.QIcon(path + 'Slope/Rgentleupslope1.png')], 
                              ['Gentle Upslope 2', QtGui.QIcon(path + 'Slope/Rgentleupslope2.png')], 
                              ['Gentle Upslope 3', QtGui.QIcon(path + 'Slope/Rgentleupslope3.png')], 
                              ['Gentle Upslope 4', QtGui.QIcon(path + 'Slope/Rgentleupslope4.png')]]
        
        SpikeParams = [['Double Left Spikes', QtGui.QIcon(path + 'Spike/Left.png')], 
                       ['Double Right Spikes', QtGui.QIcon(path + 'Spike/Right.png')], 
                       ['Double Upwards Spikes', QtGui.QIcon(path + 'Spike/Up.png')], 
                       ['Double Downwards Spikes', QtGui.QIcon(path + 'Spike/Down.png')], 
                       ['Long Spike Down 1', QtGui.QIcon(path + 'Spike/LongDown1.png')], 
                       ['Long Spike Down 2', QtGui.QIcon(path + 'Spike/LongDown2.png')], 
                       ['Single Downwards Spike', QtGui.QIcon(path + 'Spike/SingDown.png')], 
                       ['Spike Block', QtGui.QIcon(path + 'Unknown.png')]]
        
        ConveyorBeltParams = [['Slow', QtGui.QIcon(path + 'Unknown.png')], 
                              ['Fast', QtGui.QIcon(path + 'Unknown.png')]]
        
        
        self.ParameterList = [GenericParams, 
                              SlopeParams, 
                              ReverseSlopeParams, 
                              PartialBlockParams, 
                              CoinParams, 
                              ExplodableBlockParams,
                              ClimableGridParams, 
                              SpikeParams,
                              PipeParams, 
                              RailParams, 
                              ConveyorBeltParams]
        
        
        layout = QtGui.QGridLayout()
        layout.addWidget(self.coreType, 0, 1)
        layout.addWidget(self.propertyGroup, 0, 0, 3, 1)
        layout.addWidget(self.terrainType, 2, 1)
        layout.addWidget(self.parameters, 1, 1)
        self.setLayout(layout)


    def swapParams(self):
        for item in range(11):
            if self.coreWidgets[item].isChecked():
                self.parameters.clear()
                for option in self.ParameterList[item]:
                    self.parameters.addItem(option[1], option[0])
                    
            
            
#############################################################################################
######################### InfoBox Custom Widget to display info to ##########################
           
            
class InfoBox(QtGui.QWidget):
    def __init__(self, window):
        super(InfoBox, self).__init__(window)
    
        # InfoBox
        superLayout = QtGui.QGridLayout()
        infoLayout = QtGui.QFormLayout()
        
        self.imageBox = QtGui.QGroupBox()
        imageLayout = QtGui.QHBoxLayout()
        
        pix = QtGui.QPixmap(24, 24)
        pix.fill(QtCore.Qt.transparent)
        
        self.coreImage = QtGui.QLabel()
        self.coreImage.setPixmap(pix)
        self.terrainImage = QtGui.QLabel()
        self.terrainImage.setPixmap(pix)
        self.parameterImage = QtGui.QLabel()
        self.parameterImage.setPixmap(pix)
                
        
        self.collisionOverlay = QtGui.QCheckBox('Overlay Collision')
        self.collisionOverlay.clicked.connect(window.tileDisplay.update)
        
        
        self.coreInfo = QtGui.QLabel()
        self.propertyInfo = QtGui.QLabel('             \n\n\n\n\n')
        self.terrainInfo = QtGui.QLabel()
        self.paramInfo = QtGui.QLabel()

        Font = self.font()
        Font.setPointSize(9)

        self.coreInfo.setFont(Font)
        self.propertyInfo.setFont(Font)
        self.terrainInfo.setFont(Font)
        self.paramInfo.setFont(Font)
        

        self.LabelB = QtGui.QLabel('Properties:')
        self.LabelB.setFont(Font)

        self.hexdata = QtGui.QLabel('Hex Data: 0x00 0x00 0x00 0x00\n                0x00 0x00 0x00 0x00')
        self.hexdata.setFont(Font)


        coreLayout = QtGui.QVBoxLayout()
        terrLayout = QtGui.QVBoxLayout()
        paramLayout = QtGui.QVBoxLayout()

        coreLayout.setGeometry(QtCore.QRect(0,0,40,40))
        terrLayout.setGeometry(QtCore.QRect(0,0,40,40))
        paramLayout.setGeometry(QtCore.QRect(0,0,40,40))

        
        label = QtGui.QLabel('Core')
        label.setFont(Font)
        coreLayout.addWidget(label, 0, QtCore.Qt.AlignCenter)

        label = QtGui.QLabel('Terrain')
        label.setFont(Font)
        terrLayout.addWidget(label, 0, QtCore.Qt.AlignCenter)

        label = QtGui.QLabel('Parameters')
        label.setFont(Font)
        paramLayout.addWidget(label, 0, QtCore.Qt.AlignCenter)

        coreLayout.addWidget(self.coreImage, 0, QtCore.Qt.AlignCenter)
        terrLayout.addWidget(self.terrainImage, 0, QtCore.Qt.AlignCenter)
        paramLayout.addWidget(self.parameterImage, 0, QtCore.Qt.AlignCenter)

        coreLayout.addWidget(self.coreInfo, 0, QtCore.Qt.AlignCenter)
        terrLayout.addWidget(self.terrainInfo, 0, QtCore.Qt.AlignCenter)
        paramLayout.addWidget(self.paramInfo, 0, QtCore.Qt.AlignCenter)
 
        imageLayout.setContentsMargins(0,4,4,4)
        imageLayout.addLayout(coreLayout)
        imageLayout.addLayout(terrLayout)
        imageLayout.addLayout(paramLayout)

        self.imageBox.setLayout(imageLayout)

        
        superLayout.addWidget(self.imageBox, 0, 0)
        superLayout.addWidget(self.collisionOverlay, 1, 0)
        infoLayout.addRow(self.LabelB, self.propertyInfo)
        infoLayout.addRow(self.hexdata)
        superLayout.addLayout(infoLayout, 0, 1, 2, 1)
        self.setLayout(superLayout)
            
            


#############################################################################################
##################### Object List Widget and Model Setup with Painter #######################


class objectList(QtGui.QListView):
        
    def __init__(self, parent=None):
        super(objectList, self).__init__(parent)


        self.setViewMode(QtGui.QListView.IconMode)
        self.setIconSize(QtCore.QSize(96,96))
        self.setGridSize(QtCore.QSize(114,114))
        self.setMovement(QtGui.QListView.Static)
        self.setBackgroundRole(QtGui.QPalette.BrightText)
        self.setWrapping(False)
        self.setMinimumHeight(140)
        self.setMaximumHeight(140)

        

def SetupObjectModel(self, objects, tiles):
    global Tileset
    self.clear()
    
    count = 0
    for object in objects:
        tex = QtGui.QPixmap(object.width * 24, object.height * 24)
        tex.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(tex)
        
        Xoffset = 0
        Yoffset = 0
        
        for i in range(len(object.tiles)):
            for tile in object.tiles[i]:
                if (Tileset.slot == 0) or ((tile[2] & 3) != 0):
                    painter.drawPixmap(Xoffset, Yoffset, tiles[tile[1]].image)
                Xoffset += 24
            Xoffset = 0
            Yoffset += 24
                        
        painter.end()

        self.appendRow(QtGui.QStandardItem(QtGui.QIcon(tex), 'Object {0}'.format(count)))
    
        count += 1


#############################################################################################
######################## List Widget with custom painter/MouseEvent #########################


class displayWidget(QtGui.QListView):
    
    mouseMoved = QtCore.pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super(displayWidget, self).__init__(parent)

        self.setMinimumWidth(424)
        self.setMaximumWidth(424)
        self.setMinimumHeight(404)
        self.setDragEnabled(True)
        self.setViewMode(QtGui.QListView.IconMode)
        self.setIconSize(QtCore.QSize(24,24))
        self.setGridSize(QtCore.QSize(25,25))
        self.setMovement(QtGui.QListView.Static)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(True)
        self.setResizeMode(QtGui.QListView.Adjust)
        self.setUniformItemSizes(True)
        self.setBackgroundRole(QtGui.QPalette.BrightText)
        self.setMouseTracking(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.setItemDelegate(self.TileItemDelegate())


    def mouseMoveEvent(self, event):
        QtGui.QWidget.mouseMoveEvent(self, event)
        
        self.mouseMoved.emit(event.x(), event.y())
        
                
                
    class TileItemDelegate(QtGui.QAbstractItemDelegate):
        """Handles tiles and their rendering"""
        
        def __init__(self):
            """Initialises the delegate"""
            QtGui.QAbstractItemDelegate.__init__(self)
        
        def paint(self, painter, option, index):
            """Paints an object"""

            global Tileset
            p = index.model().data(index, QtCore.Qt.DecorationRole)
            painter.drawPixmap(option.rect.x(), option.rect.y(), p.pixmap(24,24))

            x = option.rect.x()
            y = option.rect.y()


            # Collision Overlays
            info = window.infoDisplay
            curTile = Tileset.tiles[index.row()]
            
            if info.collisionOverlay.isChecked():
                path = os.path.dirname(os.path.abspath(sys.argv[0])) + '/Icons/'
                
                # Sets the colour based on terrain type
                if curTile.byte2 & 16:      # Red
                    colour = QtGui.QColor(255, 0, 0, 120)                    
                elif curTile.byte5 == 1:    # Ice
                    colour = QtGui.QColor(0, 0, 255, 120)
                elif curTile.byte5 == 2:    # Snow
                    colour = QtGui.QColor(0, 0, 255, 120)
                elif curTile.byte5 == 3:    # Quicksand
                    colour = QtGui.QColor(128,64,0, 120)
                elif curTile.byte5 == 4:    # Conveyor
                    colour = QtGui.QColor(128,128,128, 120)
                elif curTile.byte5 == 5:    # Conveyor
                    colour = QtGui.QColor(128,128,128, 120)
                elif curTile.byte5 == 6:    # Rope
                    colour = QtGui.QColor(128,0,255, 120)
                elif curTile.byte5 == 7:    # Half Spike
                    colour = QtGui.QColor(128,0,255, 120)
                elif curTile.byte5 == 8:    # Ledge
                    colour = QtGui.QColor(128,0,255, 120)
                elif curTile.byte5 == 9:    # Ladder
                    colour = QtGui.QColor(128,0,255, 120)
                elif curTile.byte5 == 10:    # Staircase
                    colour = QtGui.QColor(255, 0, 0, 120)
                elif curTile.byte5 == 11:    # Carpet
                    colour = QtGui.QColor(255, 0, 0, 120)
                elif curTile.byte5 == 12:    # Dust
                    colour = QtGui.QColor(128,64,0, 120)
                elif curTile.byte5 == 13:    # Grass
                    colour = QtGui.QColor(0, 255, 0, 120)
                elif curTile.byte5 == 14:    # Unknown
                    colour = QtGui.QColor(255, 0, 0, 120)
                elif curTile.byte5 == 15:    # Beach Sand
                    colour = QtGui.QColor(128, 64, 0, 120)
                else:                       # Brown?
                    colour = QtGui.QColor(64, 30, 0, 120)


                # Sets Brush style for fills
                if curTile.byte2 & 4:        # Climbing Grid
                    style = QtCore.Qt.DiagCrossPattern
                elif curTile.byte3 & 16:     # Breakable
                    style = QtCore.Qt.VerPattern
                else:
                    style = QtCore.Qt.SolidPattern


                brush = QtGui.QBrush(colour, style)
                painter.setBrush(brush)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)


                # Paints shape based on other junk
                if curTile.byte3 & 32: # Slope
                    if curTile.byte7 == 0:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y)]))
                    elif curTile.byte7 == 1:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 2:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y + 12)]))
                    elif curTile.byte7 == 3:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 24)]))
                    elif curTile.byte7 == 4:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x + 24, y + 24)]))
                    elif curTile.byte7 == 5:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 10:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y)]))
                    elif curTile.byte7 == 11:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 24, y + 18),
                                                            QtCore.QPoint(x + 24, y + 24)]))
                    elif curTile.byte7 == 12:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x, y + 18),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 13:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y + 6),
                                                            QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 14:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x, y + 6),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 15:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y + 6),
                                                            QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 16:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x, y + 6),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 17:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y + 18),
                                                            QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 18:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x, y + 18),
                                                            QtCore.QPoint(x, y + 24)]))

                elif curTile.byte3 & 64: # Reverse Slope
                    if curTile.byte7 == 0:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y)]))
                    elif curTile.byte7 == 1:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y)]))
                    elif curTile.byte7 == 2:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y + 12)]))
                    elif curTile.byte7 == 3:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y)]))
                    elif curTile.byte7 == 4:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12)]))
                    elif curTile.byte7 == 5:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y)]))
                    elif curTile.byte7 == 10:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y)]))
                    elif curTile.byte7 == 11:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 6)]))
                    elif curTile.byte7 == 12:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x, y + 6)]))
                    elif curTile.byte7 == 13:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 18),
                                                            QtCore.QPoint(x, y + 12)]))
                    elif curTile.byte7 == 14:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x, y + 18)]))
                    elif curTile.byte7 == 15:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 18),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 16:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x, y + 18)]))
                    elif curTile.byte7 == 17:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 6),
                                                            QtCore.QPoint(x, y + 12)]))
                    elif curTile.byte7 == 18:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x, y + 6)]))

                elif curTile.byte2 & 8: # Partial
                    if curTile.byte7 == 1:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 12, y + 12),
                                                            QtCore.QPoint(x, y + 12)]))
                    elif curTile.byte7 == 2:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x + 12, y + 12)]))
                    elif curTile.byte7 == 3:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x, y + 12)]))
                    elif curTile.byte7 == 4:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x + 12, y + 12),
                                                            QtCore.QPoint(x + 12, y + 24),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 5:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 12, y + 24),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 6:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 12, y + 24),
                                                            QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x, y + 12)]))
                    elif curTile.byte7 == 7:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x + 12, y + 12),
                                                            QtCore.QPoint(x + 12, y + 24),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 8:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 12, y + 12),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 12, y + 24)]))
                    elif curTile.byte7 == 9:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 12, y + 24),
                                                            QtCore.QPoint(x + 12, y)]))
                    elif curTile.byte7 == 10:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 12, y + 24)]))
                    elif curTile.byte7 == 11:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 12, y + 24),
                                                            QtCore.QPoint(x + 12, y + 12),
                                                            QtCore.QPoint(x, y + 12)]))
                    elif curTile.byte7 == 12:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 13:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 12, y + 12),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 14:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 12, y + 12),
                                                            QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x, y + 24)]))
                    elif curTile.byte7 == 15:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x, y + 24)]))

                elif curTile.byte2 & 0x20: # Solid-on-bottom
                    painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                        QtCore.QPoint(x + 24, y + 24),
                                                        QtCore.QPoint(x + 24, y + 18),
                                                        QtCore.QPoint(x, y + 18)]))

                    painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 15, y),
                                                        QtCore.QPoint(x + 15, y + 12),
                                                        QtCore.QPoint(x + 18, y + 12),
                                                        QtCore.QPoint(x + 12, y + 17),
                                                        QtCore.QPoint(x + 6, y + 12),
                                                        QtCore.QPoint(x + 9, y + 12),
                                                        QtCore.QPoint(x + 9, y)]))

                elif curTile.byte2 & 0x80: # Solid-on-top
                    painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                        QtCore.QPoint(x + 24, y),
                                                        QtCore.QPoint(x + 24, y + 6),
                                                        QtCore.QPoint(x, y + 6)]))

                    painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 15, y + 24),
                                                        QtCore.QPoint(x + 15, y + 12),
                                                        QtCore.QPoint(x + 18, y + 12),
                                                        QtCore.QPoint(x + 12, y + 7),
                                                        QtCore.QPoint(x + 6, y + 12),
                                                        QtCore.QPoint(x + 9, y + 12),
                                                        QtCore.QPoint(x + 9, y + 24)]))

                elif curTile.byte2 & 16: # Spikes
                    if curTile.byte7 == 0:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x, y + 6)]))
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 24, y + 12),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x, y + 18)]))
                    if curTile.byte7 == 1:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x + 24, y + 6)]))
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 12),
                                                            QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 24, y + 18)]))
                    if curTile.byte7 == 2:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y + 24),
                                                            QtCore.QPoint(x + 12, y + 24),
                                                            QtCore.QPoint(x + 6, y)]))
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 12, y + 24),
                                                            QtCore.QPoint(x + 24, y + 24),
                                                            QtCore.QPoint(x + 18, y)]))
                    if curTile.byte7 == 3:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 6, y + 24)]))
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 12, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 18, y + 24)]))
                    if curTile.byte7 == 4:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 18, y + 24),
                                                            QtCore.QPoint(x + 6, y + 24)]))
                    if curTile.byte7 == 5:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x + 6, y),
                                                            QtCore.QPoint(x + 18, y),
                                                            QtCore.QPoint(x + 12, y + 24)]))
                    if curTile.byte7 == 6:
                        painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(x, y),
                                                            QtCore.QPoint(x + 24, y),
                                                            QtCore.QPoint(x + 12, y + 24)]))

                elif curTile.byte3 & 4: # QBlock
                    if curTile.byte7 == 0:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/FireF.png'))
                    if curTile.byte7 == 1:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Star.png'))
                    if curTile.byte7 == 2:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Coin.png'))
                    if curTile.byte7 == 3:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Vine.png'))
                    if curTile.byte7 == 4:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/1up.png'))
                    if curTile.byte7 == 5:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Mini.png'))
                    if curTile.byte7 == 6:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Prop.png'))
                    if curTile.byte7 == 7:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Peng.png'))                    
                    if curTile.byte7 == 8:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/IceF.png'))

                elif curTile.byte3 & 2: # Coin
                    if curTile.byte7 == 0:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Coin/Coin.png'))
                    if curTile.byte7 == 4:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Coin/POW.png'))

                elif curTile.byte3 & 8: # Exploder
                    if curTile.byte7 == 1:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Explode/Stone.png'))
                    if curTile.byte7 == 2:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Explode/Wood.png'))
                    if curTile.byte7 == 3:
                        painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Explode/Red.png'))

                elif curTile.byte1 & 2: # Falling
                    painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Prop/Fall.png'))

#                elif curTile.byte5 == 4 or 5: # Conveyor
#                    d

                elif curTile.byte3 & 1: # Solid
                    painter.drawRect(option.rect)

                else: # No fill
                    pass
                                

            # Highlight stuff. 
            colour = QtGui.QColor(option.palette.highlight())
            colour.setAlpha(80)

            if option.state & QtGui.QStyle.State_Selected:
                painter.fillRect(option.rect, colour)
            
        
        def sizeHint(self, option, index):
            """Returns the size for the object"""
            return QtCore.QSize(24,24)
        
        
        
#############################################################################################
############################ Tile widget for drag n'drop Objects ############################


class tileOverlord(QtGui.QWidget):

    def __init__(self):
        super(tileOverlord, self).__init__()

        # Setup Widgets
        self.tiles = tileWidget()

        self.addObject = QtGui.QPushButton('Add')
        self.removeObject = QtGui.QPushButton('Remove')

        self.addRow = QtGui.QPushButton('+')
        self.removeRow = QtGui.QPushButton('-')
    
        self.addColumn = QtGui.QPushButton('+')
        self.removeColumn = QtGui.QPushButton('-')

        self.tilingMethod = QtGui.QComboBox()
        self.tilesetType = QtGui.QLabel('Pa0')

        self.tilingMethod.addItems(['Repeat', 
                                    'Stretch Center',
                                    'Stretch X',
                                    'Stretch Y',
                                    'Repeat Bottom',
                                    'Repeat Top',
                                    'Repeat Left',
                                    'Repeat Right',
                                    'Upward slope',
                                    'Downward slope',
                                    'Downward reverse slope',
                                    'Upward reverse slope'])


        # Connections
        self.addObject.released.connect(self.addObj)
        self.removeObject.released.connect(self.removeObj)
        self.addRow.released.connect(self.tiles.addRow)
        self.removeRow.released.connect(self.tiles.removeRow)
        self.addColumn.released.connect(self.tiles.addColumn)
        self.removeColumn.released.connect(self.tiles.removeColumn)

        self.tilingMethod.activated.connect(self.setTiling)


        # Layout
        layout = QtGui.QGridLayout()        
        
        layout.addWidget(self.tilesetType, 0, 0, 1, 3)
        layout.addWidget(self.tilingMethod, 0, 3, 1, 3)

        layout.addWidget(self.addObject, 0, 6, 1, 1)
        layout.addWidget(self.removeObject, 0, 7, 1, 1)
        
        layout.setRowMinimumHeight(1, 40)
        
        layout.setRowStretch(1, 1)
        layout.setRowStretch(2, 5)
        layout.setRowStretch(5, 5)
        layout.addWidget(self.tiles, 2, 1, 4, 6)
        
        layout.addWidget(self.addColumn, 3, 7, 1, 1)
        layout.addWidget(self.removeColumn, 4, 7, 1, 1)
        layout.addWidget(self.addRow, 6, 3, 1, 1)
        layout.addWidget(self.removeRow, 6, 4, 1, 1)
        
        self.setLayout(layout)
       



    def addObj(self):
        global Tileset
        
        Tileset.addObject()
        
        pix = QtGui.QPixmap(24, 24)
        pix.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pix)
        painter.drawPixmap(0, 0, Tileset.tiles[0].image)
        painter.end()
                    
        count = len(Tileset.objects)
        window.objmodel.appendRow(QtGui.QStandardItem(QtGui.QIcon(pix), 'Object {0}'.format(count-1)))
        index = window.objectList.currentIndex()
        window.objectList.setCurrentIndex(index)
        self.setObject(index)

        window.objectList.update()
        self.update()
        

    def removeObj(self):
        global Tileset

        index = window.objectList.currentIndex()

        Tileset.removeObject(index.row())
        window.objmodel.removeRow(index.row())
        self.tiles.clear()

        window.objectList.update()
        self.update()


    def setObject(self, index):
        global Tileset
        object = Tileset.objects[index.row()]
                
        width = len(object.tiles[0])-1
        height = len(object.tiles)-1
        Xuniform = True
        Yuniform = True
        Xstretch = False
        Ystretch = False

        for tile in object.tiles[0]:
            if tile[0] != object.tiles[0][0][0]:
                Xuniform = False
                
        for tile in object.tiles:
            if tile[0][0] != object.tiles[0][0][0]:
                Yuniform = False

        if object.tiles[0][0][0] == object.tiles[0][width][0] and Xuniform == False:
            Xstretch = True

        if object.tiles[0][0][0] == object.tiles[height][0][0] and Xuniform == False:
            Ystretch = True



        if object.upperslope[0] != 0:
            if object.upperslope[0] == 0x90:
                self.tilingMethod.setCurrentIndex(8)
            elif object.upperslope[0] == 0x91:
                self.tilingMethod.setCurrentIndex(9)
            elif object.upperslope[0] == 0x92:
                self.tilingMethod.setCurrentIndex(10)
            elif object.upperslope[0] == 0x93:
                self.tilingMethod.setCurrentIndex(11)
            
        else:
            if Xuniform and Yuniform:
                self.tilingMethod.setCurrentIndex(0)
            elif Xstretch and Ystretch:
                self.tilingMethod.setCurrentIndex(1)
            elif Xstretch:
                self.tilingMethod.setCurrentIndex(2)
            elif Ystretch:
                self.tilingMethod.setCurrentIndex(3)
            elif Xuniform and Yuniform == False and object.tiles[0][0][0] == 0:
                self.tilingMethod.setCurrentIndex(4)
            elif Xuniform and Yuniform == False and object.tiles[height][0][0] == 0:
                self.tilingMethod.setCurrentIndex(5)
            elif Xuniform == False and Yuniform and object.tiles[0][0][0] == 0:
                self.tilingMethod.setCurrentIndex(6)
            elif Xuniform == False and Yuniform and object.tiles[0][width][0] == 0:
                self.tilingMethod.setCurrentIndex(7)

                
        self.tiles.setObject(object)

#        print 'Object {0}, Width: {1} / Height: {2}, Slope {3}/{4}'.format(index.row(), object.width, object.height, object.upperslope, object.lowerslope)
#        for row in object.tiles:
#            print 'Row: {0}'.format(row)
#        print ''
    
    @QtCore.pyqtSlot(int)
    def setTiling(self, listindex):
        global Tileset
        
        index = window.objectList.currentIndex()
        object = Tileset.objects[index.row()]
        
        
        if listindex == 0: # Repeat
            ctile = 0
            crow = 0

            for row in object.tiles:
                for tile in row:
                    object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0
                
        if listindex == 1: # Stretch Center

            if object.width < 3 and object.height < 3:
                reply = QtGui.QMessageBox.information(self, "Warning", "An object must be at least 3 tiles\nwide and 3 tiles tall to apply stretch center.")
                self.setObject(index)
                return
                
            ctile = 0
            crow = 0

            for row in object.tiles:
                for tile in row:
                    if crow == 0 and ctile == 0:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    elif crow == 0 and ctile == object.width-1:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    elif crow == object.height-1 and ctile == object.width-1:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    elif crow == object.height-1 and ctile == 0:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    elif crow == 0 or crow == object.height-1:
                        object.tiles[crow][ctile] = (1, tile[1], tile[2])
                    elif ctile == 0 or ctile == object.width-1:
                        object.tiles[crow][ctile] = (2, tile[1], tile[2])
                    else:
                        object.tiles[crow][ctile] = (3, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0

        if listindex == 2: # Stretch X

            if object.width < 3:
                reply = QtGui.QMessageBox.information(self, "Warning", "An object must be at least 3 tiles\nwide to apply stretch X.")
                self.setObject(index)
                return
                
            ctile = 0
            crow = 0

            for row in object.tiles:
                for tile in row:
                    if ctile == 0:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    elif ctile == object.width-1:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    else:
                        object.tiles[crow][ctile] = (1, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0
                
        if listindex == 3: # Stretch Y

            if object.height < 3:
                reply = QtGui.QMessageBox.information(self, "Warning", "An object must be at least 3 tiles\ntall to apply stretch Y.")
                self.setObject(index)
                return
                
            ctile = 0
            crow = 0

            for row in object.tiles:
                for tile in row:
                    if crow == 0:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    elif crow == object.height-1:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    else:
                        object.tiles[crow][ctile] = (2, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0
                
        if listindex == 4: # Repeat Bottom

            if object.height < 2:
                reply = QtGui.QMessageBox.information(self, "Warning", "An object must be at least 2 tiles\ntall to apply repeat bottom.")
                self.setObject(index)
                return
                
            ctile = 0
            crow = 0

            for row in object.tiles:
                for tile in row:
                    if crow == object.height-1:
                        object.tiles[crow][ctile] = (2, tile[1], tile[2])
                    else:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0

        if listindex == 5: # Repeat Top

            if object.height < 2:
                reply = QtGui.QMessageBox.information(self, "Warning", "An object must be at least 2 tiles\ntall to apply repeat top.")
                self.setObject(index)
                return
                
            ctile = 0
            crow = 0

            for row in object.tiles:
                for tile in row:
                    if crow == 0:
                        object.tiles[crow][ctile] = (2, tile[1], tile[2])
                    else:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0

        if listindex == 6: # Repeat Left

            if object.width < 2:
                reply = QtGui.QMessageBox.information(self, "Warning", "An object must be at least 2 tiles\nwide to apply repeat left.")
                self.setObject(index)
                return
                
            ctile = 0
            crow = 0

            for row in object.tiles:
                for tile in row:
                    if ctile == 0:
                        object.tiles[crow][ctile] = (1, tile[1], tile[2])
                    else:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0

        if listindex == 7: # Repeat Right

            if object.width < 2:
                reply = QtGui.QMessageBox.information(self, "Warning", "An object must be at least 2 tiles\nwide to apply repeat right.")
                self.setObject(index)
                return
                
            ctile = 0
            crow = 0

            for row in object.tiles:
                for tile in row:
                    if ctile == object.width-1:
                        object.tiles[crow][ctile] = (1, tile[1], tile[2])
                    else:
                        object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0


        if listindex == 8: # Upward Slope
            ctile = 0
            crow = 0
            for row in object.tiles:
                for tile in row:
                    object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0

            object.upperslope = [0x90, 1]
            object.lowerslope = [0x84, object.height - 1]
            self.tiles.slope = 1
            
            self.tiles.update()
            
        if listindex == 9: # Downware Slope
            ctile = 0
            crow = 0
            for row in object.tiles:
                for tile in row:
                    object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0

            object.upperslope = [0x91, 1]
            object.lowerslope = [0x84, object.height - 1]
            self.tiles.slope = 1
            
            self.tiles.update()

        if listindex == 10: # Upward Reverse Slope
            ctile = 0
            crow = 0
            for row in object.tiles:
                for tile in row:
                    object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0

            object.upperslope = [0x92, object.height - 1]
            object.lowerslope = [0x84, 1]
            self.tiles.slope = 0-(object.height-1)
            
            self.tiles.update()

        if listindex == 11: # Downward Reverse Slope
            ctile = 0
            crow = 0
            for row in object.tiles:
                for tile in row:
                    object.tiles[crow][ctile] = (0, tile[1], tile[2])
                    ctile += 1
                crow += 1
                ctile = 0

            object.upperslope = [0x93, object.height - 1]
            object.lowerslope = [0x84, 1]
            self.tiles.slope = 0-(object.height-1)
            
            self.tiles.update()
       

class tileWidget(QtGui.QWidget):
    
    def __init__(self):
        super(tileWidget, self).__init__()

        self.tiles = []

        self.size = [1, 1]
        self.setMinimumSize(24, 24)

        self.slope = 0

        self.highlightedRect = QtCore.QRect()

        self.setAcceptDrops(True)
        self.object = 0


    def clear(self):
        self.tiles = []
        self.size = [1, 1] # [width, height]
        
        self.slope = 0
        self.highlightedRect = QtCore.QRect()

        self.update()


    def addColumn(self):
        global Tileset
        
        if self.size[0] >= 24:
            return
            
        self.size[0] += 1
        self.setMinimumSize(self.size[0]*24, self.size[1]*24)

        pix = QtGui.QPixmap(24,24)
        pix.fill(QtGui.QColor(0,0,0,0))

        for y in xrange(self.size[1]):
            self.tiles.insert(((y+1) * self.size[0]) -1, [self.size[0]-1, y, pix])

 
        curObj = Tileset.objects[self.object]
        curObj.width += 1

        for row in curObj.tiles:
            row.append((0, 0, 0))
            
        self.update()
        self.updateList()

   
    def removeColumn(self):
        global Tileset

        if self.size[0] == 1:
            return

        for y in xrange(self.size[1]):
            self.tiles.pop(((y+1) * self.size[0])-(y+1))

        self.size[0] = self.size[0] - 1
        self.setMinimumSize(self.size[0]*24, self.size[1]*24)


        curObj = Tileset.objects[self.object]
        curObj.width -= 1

        for row in curObj.tiles:
            row.pop()

        self.update()
        self.updateList()


    def addRow(self):
        global Tileset

        if self.size[1] >= 24:
            return
        
        self.size[1] += 1
        self.setMinimumSize(self.size[0]*24, self.size[1]*24)

        pix = QtGui.QPixmap(24,24)
        pix.fill(QtGui.QColor(0,0,0,0))

        for x in xrange(self.size[0]):
            self.tiles.append([x, self.size[1]-1, pix])

        curObj = Tileset.objects[self.object]
        curObj.height += 1

        curObj.tiles.append([])
        for i in xrange(0, curObj.width):
            curObj.tiles[len(curObj.tiles)-1].append((0, 0, 0))

        self.update()
        self.updateList()

    
    def removeRow(self):
        global Tileset

        if self.size[1] == 1:
            return

        for x in xrange(self.size[0]):
            self.tiles.pop()
        
        self.size[1] -= 1
        self.setMinimumSize(self.size[0]*24, self.size[1]*24)

        curObj = Tileset.objects[self.object]
        curObj.height -= 1

        curObj.tiles.pop()

        self.update()
        self.updateList()


    def setObject(self, object):
        self.clear()
            
        global Tileset
            
        self.size = [object.width, object.height]
        
        if not object.upperslope[1] == 0:
            if object.upperslope[0] & 2:
                self.slope = 0 - object.lowerslope[1]
            else:
                self.slope = object.upperslope[1]

        x = 0
        y = 0
        for row in object.tiles:
            for tile in row:
                if (Tileset.slot == 0) or ((tile[2] & 3) != 0):
                    self.tiles.append([x, y, Tileset.tiles[tile[1]].image])
                else:
                    pix = QtGui.QPixmap(24,24)
                    pix.fill(QtGui.QColor(0,0,0,0))
                    self.tiles.append([x, y, pix])
                x += 1
            y += 1
            x = 0
           
           
        self.object = window.objectList.currentIndex().row()    
        self.update()
        self.updateList()
               

    def contextMenuEvent(self, event):
    
        TileMenu = QtGui.QMenu(self)
        self.contX = event.x()
        self.contY = event.y()
        
        TileMenu.addAction('Set tile...', self.setTile)
        TileMenu.addAction('Add Item...', self.setItem)

        TileMenu.exec_(event.globalPos())


    def mousePressEvent(self, event):
        global Tileset

        if event.button() == 2:
            return

        if window.tileDisplay.selectedIndexes() == []:
            return

        currentSelected = window.tileDisplay.selectedIndexes()
        
        ix = 0
        iy = 0
        for modelItem in currentSelected:
            # Update yourself!
            centerPoint = self.contentsRect().center()
    
            tile = modelItem.row()
            upperLeftX = centerPoint.x() - self.size[0]*12
            upperLeftY = centerPoint.y() - self.size[1]*12
    
            lowerRightX = centerPoint.x() + self.size[0]*12
            lowerRightY = centerPoint.y() + self.size[1]*12
    
    
            x = (event.x() - upperLeftX)/24 + ix
            y = (event.y() - upperLeftY)/24 + iy
    
            if event.x() < upperLeftX or event.y() < upperLeftY or event.x() > lowerRightX or event.y() > lowerRightY:
                return
                    
            self.tiles[(y * self.size[0]) + x][2] = Tileset.tiles[tile].image
                    
            Tileset.objects[self.object].tiles[y][x] = (Tileset.objects[self.object].tiles[y][x][0], tile, Tileset.slot)
            

            ix += 1
            if self.size[0]-1 < ix:
                ix = 0
                iy += 1
            if iy > self.size[1]-1:
                break
            
            
        self.update()
        
        self.updateList()
        

    def updateList(self):        
        # Update the list >.>
        object = window.objmodel.itemFromIndex(window.objectList.currentIndex())
        
        
        tex = QtGui.QPixmap(self.size[0] * 24, self.size[1] * 24)
        tex.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(tex)
        
        Xoffset = 0
        Yoffset = 0
        
        for tile in self.tiles:
            painter.drawPixmap(tile[0]*24, tile[1]*24, tile[2])
                        
        painter.end()

        object.setIcon(QtGui.QIcon(tex))

        window.objectList.update()
    
            
        
    def setTile(self):
        global Tileset
        
        dlg = self.setTileDialog()
        if dlg.exec_() == QtGui.QDialog.Accepted:
            # Do stuff
            centerPoint = self.contentsRect().center()

            upperLeftX = centerPoint.x() - self.size[0]*12
            upperLeftY = centerPoint.y() - self.size[1]*12

            tile = dlg.tile.value()
            tileset = dlg.tileset.currentIndex()
    
            x = (self.contX - upperLeftX)/24
            y = (self.contY - upperLeftY)/24

            if tileset != Tileset.slot:
                tex = QtGui.QPixmap(self.size[0] * 24, self.size[1] * 24)
                tex.fill(QtCore.Qt.transparent)
        
                self.tiles[(y * self.size[0]) + x][2] = tex

            Tileset.objects[self.object].tiles[y][x] = (Tileset.objects[self.object].tiles[y][x][0], tile, tileset)
            
            self.update()
            self.updateList()


    class setTileDialog(QtGui.QDialog):
    
        def __init__(self):
            QtGui.QDialog.__init__(self)
        
            self.setWindowTitle('Set tiles')
        
            self.tileset = QtGui.QComboBox()
            self.tileset.addItems(['Pa0', 'Pa1', 'Pa2', 'Pa3'])
        
            self.tile = QtGui.QSpinBox()                
            self.tile.setRange(0, 255)             
            
            self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            
            self.layout = QtGui.QGridLayout()
            self.layout.addWidget(QtGui.QLabel('Tileset:'), 0,0,1,1, QtCore.Qt.AlignLeft)
            self.layout.addWidget(QtGui.QLabel('Tile:'), 0,3,1,1, QtCore.Qt.AlignLeft)
            self.layout.addWidget(self.tileset, 1, 0, 1, 2)
            self.layout.addWidget(self.tile, 1, 3, 1, 3)
            self.layout.addWidget(self.buttons, 2, 3)
            self.setLayout(self.layout)


    def setItem(self):
        global Tileset
        
        dlg = self.setItemDialog()
        if dlg.exec_() == QtGui.QDialog.Accepted:
            # Do stuff
            centerPoint = self.contentsRect().center()

            upperLeftX = centerPoint.x() - self.size[0]*12
            upperLeftY = centerPoint.y() - self.size[1]*12

            item = dlg.item.currentIndex()
    
            x = (self.contX - upperLeftX)/24
            y = (self.contY - upperLeftY)/24

            obj = Tileset.objects[self.object].tiles[y][x]
            
            obj = (obj[0], obj[1], obj[2] | (item << 2))
            
            self.update()
            self.updateList()


    class setItemDialog(QtGui.QDialog):
    
        def __init__(self):
            QtGui.QDialog.__init__(self)
        
            self.setWindowTitle('Set item')
        
            self.item = QtGui.QComboBox()
            self.item.addItems(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14'])
                    
            self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            
            self.layout = QtGui.QHBoxLayout()
            self.vlayout = QtGui.QVBoxLayout()
            self.layout.addWidget(QtGui.QLabel('Item:'))
            self.layout.addWidget(self.item)
            self.vlayout.addLayout(self.layout)
            self.vlayout.addWidget(self.buttons)
            self.setLayout(self.vlayout)
            
               

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        
        centerPoint = self.contentsRect().center()
        upperLeftX = centerPoint.x() - self.size[0]*12
        lowerRightX = centerPoint.x() + self.size[0]*12

        upperLeftY = centerPoint.y() - self.size[1]*12
        lowerRightY = centerPoint.y() + self.size[1]*12


        painter.fillRect(upperLeftX, upperLeftY, self.size[0] * 24, self.size[1]*24, QtGui.QColor(205, 205, 255))

        for x, y, pix in self.tiles:
            painter.drawPixmap(upperLeftX + (x * 24), upperLeftY + (y * 24), pix)

        if not self.slope == 0:
            pen = QtGui.QPen()
#            pen.setStyle(QtCore.Qt.QDashLine)
            pen.setWidth(1)
            pen.setColor(QtCore.Qt.blue)
            painter.setPen(QtGui.QPen(pen))
            painter.drawLine(upperLeftX, upperLeftY + (abs(self.slope) * 24), lowerRightX, upperLeftY + (abs(self.slope) * 24))
            
            if self.slope > 0:
                main = 'Main'
                sub = 'Sub'
            elif self.slope < 0:
                main = 'Sub'
                sub = 'Main'

            font = painter.font()
            font.setPixelSize(8)
            font.setFamily('Monaco')
            painter.setFont(font)

            painter.drawText(upperLeftX+1, upperLeftY+10, main)
            painter.drawText(upperLeftX+1, upperLeftY + (abs(self.slope) * 24) + 9, sub)

        painter.end()



#############################################################################################
############################ Subclassed one dimension Item Model ############################


class PiecesModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super(PiecesModel, self).__init__(parent)

        self.pixmaps = []
        self.setSupportedDragActions(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction | QtCore.Qt.LinkAction)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == QtCore.Qt.DecorationRole:
            return QtGui.QIcon(self.pixmaps[index.row()])

        if role == QtCore.Qt.UserRole:
            return self.pixmaps[index.row()]

        return None

    def addPieces(self, pixmap):
        row = len(self.pixmaps)

        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.pixmaps.insert(row, pixmap)
        self.endInsertRows()
        
    def flags(self,index):
        if index.isValid():
            return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable |
                    QtCore.Qt.ItemIsDragEnabled)

    def clear(self):
        row = len(self.pixmaps)

        del self.pixmaps[:]


    def mimeTypes(self):
        return ['image/x-tile-piece']


    def mimeData(self, indexes):
        mimeData = QtCore.QMimeData()
        encodedData = QtCore.QByteArray()

        stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.WriteOnly)

        for index in indexes:
            if index.isValid():
                pixmap = QtGui.QPixmap(self.data(index, QtCore.Qt.UserRole))
                stream << pixmap

        mimeData.setData('image/x-tile-piece', encodedData)
        return mimeData


    def rowCount(self, parent):
        if parent.isValid():
            return 0
        else:
            return len(self.pixmaps)

    def supportedDragActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction



#############################################################################################
################## Python-based RGB5a3 Decoding code from my BRFNT program ##################


def RGB4A3Decode(tex):
    dest = QtGui.QImage(1024,256,QtGui.QImage.Format_ARGB32)
    dest.fill(QtCore.Qt.transparent)
    
    i = 0
    for ytile in xrange(0, 256, 4):
    	for xtile in xrange(0, 1024, 4):
    		for ypixel in xrange(ytile, ytile + 4):
    			for xpixel in xrange(xtile, xtile + 4):
    				
    				if(xpixel >= 1024 or ypixel >= 256):
    					continue
    				
    				newpixel = (tex[i] << 8) | tex[i+1]
    				
    
    				if(newpixel >= 0x8000): # Check if it's RGB555
    					red = ((newpixel >> 10) & 0x1F) * 255 / 0x1F
    					green = ((newpixel >> 5) & 0x1F) * 255 / 0x1F
    					blue = (newpixel & 0x1F) * 255 / 0x1F
    					alpha = 0xFF
    
    				else: # If not, it's RGB4A3
    					alpha = ((newpixel & 0x7000) >> 12) * 255 / 0x7
    					blue = ((newpixel & 0xF00) >> 8) * 255 / 0xF
    					green = ((newpixel & 0xF0) >> 4) * 255 / 0xF
    					red = (newpixel & 0xF) * 255 / 0xF
    
    				argb = (blue) | (green << 8) | (red << 16) | (alpha << 24)
    				dest.setPixel(xpixel, ypixel, argb)
    				i += 2
    return dest


def RGB4A3Encode(tex):
    destBuffer = create_string_buffer(524288)

    shortstruct = struct.Struct('>H')
    offset = 0

    for ytile in xrange(0, 256, 4):
        for xtile in xrange(0, 1024, 4):
            for ypixel in xrange(ytile, ytile + 4):
                for xpixel in xrange(xtile, xtile + 4):
    				
                    if(xpixel >= 1024 or ypixel >= 256):
                    	continue
                    
                    pixel = tex.pixel(xpixel, ypixel)
                    
                    a = pixel >> 24
                    r = (pixel >> 16) & 0xFF
                    g = (pixel >> 8) & 0xFF
                    b = pixel & 0xFF
                    
                    if a < 245: #RGB4A3
                        alpha = a/32
                        red = r/16
                        green = g/16
                        blue = b/16

                        rgbDAT = (blue) | (green << 4) | (red << 8) | (alpha << 12)
                
                    else: # RGB555
                        red = r/8
                        green = g/8
                        blue = b/8
                        
                        rgbDAT = (blue) | (green << 5) | (red << 10) | (0x8000) # 0rrrrrgggggbbbbb
                                                                                                            
                    shortstruct.pack_into(destBuffer, offset, rgbDAT)
                    offset += 2
                    
    return destBuffer.raw


#############################################################################################
############ Main Window Class. Takes care of menu functions and widget creation ############


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.tileImage = QtGui.QPixmap()
        self.alpha = True
        
        global Tileset
        Tileset = TilesetClass()

        self.name = ''

        self.setupMenus()
        self.setupWidgets()

        self.setuptile()

        self.newTileset()

        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,
                QtGui.QSizePolicy.Fixed))
        self.setWindowTitle("New Tileset")


    def setuptile(self):
        self.tileWidget.tiles.clear()
        self.model.clear()

        if self.alpha == True:
            for tile in Tileset.tiles:
                self.model.addPieces(tile.image)
        else:
            for tile in Tileset.tiles:
                self.model.addPieces(tile.noalpha)


    def newTileset(self):
        '''Creates a new, blank tileset'''
        
        global Tileset
        Tileset.clear()
        Tileset = TilesetClass()
        
        EmptyPix = QtGui.QPixmap(24, 24)
        EmptyPix.fill(QtCore.Qt.black)
        
        for i in range(256):
            Tileset.addTile(EmptyPix, EmptyPix)

        self.setuptile()
        self.setWindowTitle('New Tileset')
        
        
    def openTileset(self):
        '''Opens a Nintendo tileset arc and parses the heck out of it.'''
        
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open NSMBW Tileset", '',
                    "Image Files (*.arc)"))
                    
        if path:
            self.setWindowTitle(os.path.basename(path))
            Tileset.clear()

            name = path[str(path).rfind('/')+1:-4]
        
            file = open(path,'rb')
            data = file.read()
            file.close()
            
            arc = archive.U8()
            arc._load(data)
            
            Image = None
            behaviourdata = None
            objstrings = None
            metadata = None
            
            for key, value in arc.files:
                if value == None:
                    pass
                if key.startswith('BG_tex/') and key.endswith('_tex.bin.LZ'):
                    Image = arc[key]
                if key.startswith('BG_chk/d_bgchk_') and key.endswith('.bin'):
                    behaviourdata = arc[key]
                if key.startswith('BG_unt/'):
                    if key.endswith('_hd.bin'):
                        metadata = arc[key]
                    elif key.endswith('.bin'):
                        objstrings = arc[key]


            if (Image == None) or (behaviourdata == None) or (objstrings == None) or (metadata == None):
                QtGui.QMessageBox.warning(None, 'Error',  'Error - the necessary files were not found.\n\nNot a valid tileset, sadly.')
                return
            
            # Stolen from Reggie! Loads the Image Data.
            if HaveNSMBLib:
                tiledata = nsmblib.decompress11LZS(Image)
                argbdata = nsmblib.decodeTileset(tiledata)
                rgbdata = nsmblib.decodeTilesetNoAlpha(tiledata)
                dest = QtGui.QImage(argbdata, 1024, 256, 4096, QtGui.QImage.Format_ARGB32_Premultiplied)
                noalphadest = QtGui.QImage(rgbdata, 1024, 256, 4096, QtGui.QImage.Format_ARGB32_Premultiplied)
            else:
                lz = lz77.LZS11()
                dest = RGB4A3Decode(lz.Decompress11LZS(Image))
            
            self.tileImage = QtGui.QPixmap.fromImage(dest)
            noalpha = QtGui.QPixmap.fromImage(noalphadest)
            
            # Loads Tile Behaviours
                        
            behaviours = []
            for entry in range(256):
                behaviours.append(struct.unpack_from('>8B', behaviourdata, entry*8))
            
            
            # Makes us some nice Tile Classes!
            Xoffset = 4
            Yoffset = 4
            for i in range(256):
                Tileset.addTile(self.tileImage.copy(Xoffset,Yoffset,24,24), noalpha.copy(Xoffset,Yoffset,24,24), behaviours[i])
                Xoffset += 32
                if Xoffset >= 1024:
                    Xoffset = 4
                    Yoffset += 32                    
            
            
            # Load Objects
            
            meta = []
            for i in xrange(len(metadata)/4):
                meta.append(struct.unpack_from('>H2B', metadata, i * 4))                                    
                
            tilelist = [[]]
            upperslope = [0, 0]
            lowerslope = [0, 0]
            byte = 0
            
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

                Tileset.addObject(entry[2], entry[1], upperslope, lowerslope, tilelist)

                tilelist = [[]]
                upperslope = [0, 0]
                lowerslope = [0, 0]

            Tileset.slot = Tileset.objects[0].tiles[0][0][2] & 3
            self.tileWidget.tilesetType.setText('Pa{0}'.format(Tileset.slot))

            self.setuptile()
            SetupObjectModel(self.objmodel, Tileset.objects, Tileset.tiles)

        self.name = path


    def openImage(self):
        '''Opens an Image from png, and creates a new tileset from it.'''

        path = QtGui.QFileDialog.getOpenFileName(self, "Open Image", '',
                    "Image Files (*.png)")
                    
        if path:
            newImage = QtGui.QPixmap()
            self.tileImage = newImage

            if not newImage.load(path):
                QtGui.QMessageBox.warning(self, "Open Image",
                        "The image file could not be loaded.",
                        QtGui.QMessageBox.Cancel)
                return

            if ((newImage.width() == 384) & (newImage.height() == 384)):
                x = 0
                y = 0
                for i in range(256):
                    Tileset.tiles[i].image = self.tileImage.copy(x*24,y*24,24,24)
                    x += 1
                    if (x * 24) >= 384:
                        y += 1
                        x = 0

            else: 
                QtGui.QMessageBox.warning(self, "Open Image",
                        "The image was not the proper dimensions."
                        "Please resize the image to 384x384 pixels.",
                        QtGui.QMessageBox.Cancel)
                return


            self.setuptile()


    def saveImage(self):
            
        fn = QtGui.QFileDialog.getSaveFileName(self, 'Choose a new filename', '', '.png (*.png)')
        if fn == '': return
        
        tex = QtGui.QPixmap(384, 384)
        tex.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(tex)
        
        Xoffset = 0
        Yoffset = 0
        
        for tile in Tileset.tiles:
            painter.drawPixmap(Xoffset, Yoffset, tile.image)
            Xoffset += 24
            if Xoffset >= 384:
                Xoffset = 0
                Yoffset += 24
                        
        painter.end()

        tex.save(fn)
        
        
    def saveTileset(self):
        if self.name == '':
            self.saveTilesetAs()
            return
            
        
        outdata = self.saving(os.path.basename(self.name)[:-4])
        
        fn = self.name
        f = open(fn, 'wb')
        f.write(outdata)
        f.close()
                
        
    def saveTilesetAs(self):
        
        fn = QtGui.QFileDialog.getSaveFileName(self, 'Choose a new filename', '', '.arc (*.arc)')
        if fn == '': return

        self.name = fn
        self.setWindowTitle(os.path.basename(unicode(fn)))
        
        outdata = self.saving(os.path.basename(unicode(fn))[:-4])
        f = open(fn, 'wb')
        f.write(outdata)
        f.close()


    def saving(self, name):

        # Prepare tiles, objects, object metadata, and textures and stuff into buffers.

        textureBuffer = self.PackTexture()
        tileBuffer = self.PackTiles()
        objectBuffers = self.PackObjects()
        objectBuffer = objectBuffers[0]
        objectMetaBuffer = objectBuffers[1]
        
                
        # Make an arc and pack up the files!
        arc = archive.U8()
        arc['BG_tex'] = None
        arc['BG_tex/{0}_tex.bin.LZ'.format(name)] = textureBuffer

        arc['BG_chk'] = None
        arc['BG_chk/d_bgchk_{0}.bin'.format(name)] = tileBuffer

        arc['BG_unt'] = None
        arc['BG_unt/{0}.bin'.format(name)] = objectBuffer
        arc['BG_unt/{0}_hd.bin'.format(name)] = objectMetaBuffer
        
        return arc._dump()


    def PackTexture(self):

        tex = QtGui.QImage(1024, 256, QtGui.QImage.Format_ARGB32)
        tex.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(tex)
        
        Xoffset = 0
        Yoffset = 0

        for tile in Tileset.tiles:
            minitex = QtGui.QImage(32, 32, QtGui.QImage.Format_ARGB32)
            minitex.fill(QtCore.Qt.transparent)
            minipainter = QtGui.QPainter(minitex)
            
            minipainter.drawPixmap(4, 4, tile.image)
            minipainter.end()
            
            # Read colours and DESTROY THEM (or copy them to the edges, w/e)
            for i in xrange(4,28):
                
                # Top Clamp
                colour = minitex.pixel(i, 4)
                for p in xrange(0,4):
                    minitex.setPixel(i, p, colour)
                
                # Left Clamp
                colour = minitex.pixel(4, i)
                for p in xrange(0,4):
                    minitex.setPixel(p, i, colour)
                
                # Right Clamp
                colour = minitex.pixel(i, 27)
                for p in xrange(27,31):
                    minitex.setPixel(i, p, colour)
                
                # Bottom Clamp
                colour = minitex.pixel(27, i)
                for p in xrange(27,31):
                    minitex.setPixel(p, i, colour)

            # UpperLeft Corner Clamp
            colour = minitex.pixel(4, 4)
            for x in xrange(0,4):
                for y in xrange(0,4):
                    minitex.setPixel(x, y, colour)

            # UpperRight Corner Clamp
            colour = minitex.pixel(27, 4)
            for x in xrange(27,31):
                for y in xrange(0,4):
                    minitex.setPixel(x, y, colour)

            # LowerLeft Corner Clamp
            colour = minitex.pixel(4, 27)
            for x in xrange(0,4):
                for y in xrange(27,31):
                    minitex.setPixel(x, y, colour)

            # LowerRight Corner Clamp
            colour = minitex.pixel(27, 27)
            for x in xrange(27,31):
                for y in xrange(27,31):
                    minitex.setPixel(x, y, colour)

                    
            painter.drawImage(Xoffset, Yoffset, minitex)
            
            Xoffset += 32
            
            if Xoffset >= 1024:
                Xoffset = 0
                Yoffset += 32
                                    
        painter.end()

        dest = RGB4A3Encode(tex)
        
        
        items = ("Very Slow Compression, Good Quality", "Fast Compression, but the Image gets damaged")

        item, ok = QtGui.QInputDialog.getItem(self, "Choose compression method",
                "Two methods of compression are available. Choose \n"
                "Fast compression for rapid testing. Choose slow \n"
                "compression for releases. Bug Treeki to get the fast \n"
                "compression fixed.", items, 0, False)
        if ok and item == "Very Slow Compression, Good Quality":
            lz = lz77.LZS11()
            TexBuffer = (lz.Compress11LZS(dest))
        else:
            TexBuffer = nsmblib.compress11LZS(dest)
        
        return TexBuffer


    def PackTiles(self):
        offset = 0
        tilespack = struct.Struct('>8B')
        Tilebuffer = create_string_buffer(2048)
        for tile in Tileset.tiles:
            tilespack.pack_into(Tilebuffer, offset, tile.byte0, tile.byte1, tile.byte2, tile.byte3, tile.byte4, tile.byte5, tile.byte6, tile.byte7)
            offset += 8
                    
        return Tilebuffer.raw


    def PackObjects(self):
        objectStrings = []
        
        o = 0
        for object in Tileset.objects:
                 
                
            # Slopes
            if object.upperslope[0] != 0:
                
                # Reverse Slopes
                if object.upperslope[0] & 0x2:
                    a = struct.pack('>B', object.upperslope[0])
                    
                    if object.height == 1:
                        iterationsA = 0
                        iterationsB = 1
                    else:
                        iterationsA = object.upperslope[1]
                        iterationsB = object.lowerslope[1] + object.upperslope[1]
                        
                    for row in xrange(iterationsA, iterationsB):
                        for tile in object.tiles[row]:
                            a = a + struct.pack('>BBB', tile[0], tile[1], tile[2])
                        a = a + '\xfe'

                    if object.height > 1:
                        a = a + struct.pack('>B', object.lowerslope[0])
                    
                        for row in xrange(0, object.upperslope[1]):
                            for tile in object.tiles[row]:
                                a = a + struct.pack('>BBB', tile[0], tile[1], tile[2])
                            a = a + '\xfe'
                        
                    a = a + '\xff'
                    
                    objectStrings.append(a)
                    
                    
                # Regular Slopes   
                else:
                    a = struct.pack('>B', object.upperslope[0])
                    
                    for row in xrange(0, object.upperslope[1]):
                        for tile in object.tiles[row]:
                            a = a + struct.pack('>BBB', tile[0], tile[1], tile[2])
                        a = a + '\xfe'
                    
                    if object.height > 1:
                        a = a + struct.pack('>B', object.lowerslope[0])
                    
                        for row in xrange(object.upperslope[1], object.height):
                            for tile in object.tiles[row]:
                                a = a + struct.pack('>BBB', tile[0], tile[1], tile[2])
                            a = a + '\xfe'
                        
                    a = a + '\xff'
                    
                    objectStrings.append(a)
                    
                    
            # Not slopes!    
            else:
                a = ''
                
                for tilerow in object.tiles:
                    for tile in tilerow:
                        a = a + struct.pack('>BBB', tile[0], tile[1], tile[2])
                    
                    a = a + '\xfe'
                    
                a = a + '\xff'
                
                objectStrings.append(a)
            
            o += 1
            
        Objbuffer = ''
        Metabuffer = ''
        i = 0
        for a in objectStrings:
            Metabuffer = Metabuffer + struct.pack('>H2B', len(Objbuffer), Tileset.objects[i].width, Tileset.objects[i].height)
            Objbuffer = Objbuffer + a
            
            i += 1
        
        return (Objbuffer, Metabuffer)



    def setupMenus(self):
        fileMenu = self.menuBar().addMenu("&File")

        pixmap = QtGui.QPixmap(60,60)
        pixmap.fill(QtCore.Qt.black)
        icon = QtGui.QIcon(pixmap)

        self.action = fileMenu.addAction(icon, "New", self.newTileset, QtGui.QKeySequence.New)
        fileMenu.addAction("Open...", self.openTileset, QtGui.QKeySequence.Open)
        fileMenu.addAction("Import Image...", self.openImage, QtGui.QKeySequence('Ctrl+I'))
        fileMenu.addAction("Export Image...", self.saveImage, QtGui.QKeySequence('Ctrl+E'))
        fileMenu.addAction("Save", self.saveTileset, QtGui.QKeySequence.Save)
        fileMenu.addAction("Save as...", self.saveTilesetAs, QtGui.QKeySequence.SaveAs)
        fileMenu.addAction("Quit", self.close, QtGui.QKeySequence('Ctrl-Q'))

        taskMenu = self.menuBar().addMenu("&Tasks")

        taskMenu.addAction("Set Tileset Slot...", self.setSlot, QtGui.QKeySequence('Ctrl+T'))
        taskMenu.addAction("Toggle Alpha", self.toggleAlpha, QtGui.QKeySequence('Ctrl+Shift+A'))
        taskMenu.addAction("Clear Collision Data", Tileset.clearCollisions, QtGui.QKeySequence('Ctrl+Shift+Backspace'))
        taskMenu.addAction("Clear Object Data", Tileset.clearObjects, QtGui.QKeySequence('Ctrl+Alt+Backspace'))



    def setSlot(self):
        global Tileset
        
        items = ("Pa0", "Pa1", "Pa2", "Pa3")

        item, ok = QtGui.QInputDialog.getItem(self, "Set Tileset Slot",
                "Warning: \n    Setting the tileset slot will override any \n    tiles set to draw from other tilesets.", items, 0, False)
        if ok and item:
            Tileset.slot = int(item[2])      
            self.tileWidget.tilesetType.setText(item)


            cobj = 0
            crow = 0
            ctile = 0
            for object in Tileset.objects:
                for row in object.tiles:
                    for tile in row:
                        if tile != (0,0,0):
                            Tileset.objects[cobj].tiles[crow][ctile] = (tile[0], tile[1], (tile[2] & 0xFC) | int(str(item[2])))
                        if tile == (0,0,0) and ctile == 0:
                            Tileset.objects[cobj].tiles[crow][ctile] = (tile[0], tile[1], (tile[2] & 0xFC) | int(str(item[2])))
                        ctile += 1
                    crow += 1
                    ctile = 0
                cobj += 1
                crow = 0
                ctile = 0


    def toggleAlpha(self):
        # Replace Alpha Image with non-Alpha images in model
        if self.alpha == True:
            self.alpha = False
        else:
            self.alpha = True

        self.setuptile()
        

    def setupWidgets(self):
        frame = QtGui.QFrame()
        frameLayout = QtGui.QGridLayout(frame)

        # Displays the tiles
        self.tileDisplay = displayWidget()
        
        # Info Box for tile information
        self.infoDisplay = InfoBox(self)
        
        # Sets up the model for the tile pieces
        self.model = PiecesModel(self)
        self.tileDisplay.setModel(self.model)

        # Object List
        self.objectList = objectList()
        self.objmodel = QtGui.QStandardItemModel()
        SetupObjectModel(self.objmodel, Tileset.objects, Tileset.tiles)
        self.objectList.setModel(self.objmodel)

        # Creates the Tab Widget for behaviours and objects
        self.tabWidget = QtGui.QTabWidget()
        self.tileWidget = tileOverlord()
        self.paletteWidget = paletteWidget(self)

        # Second Tab
        self.container = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.objectList)
        layout.addWidget(self.tileWidget)
        self.container.setLayout(layout)

        # Sets the Tabs
        self.tabWidget.addTab(self.paletteWidget, 'Behaviours')
        self.tabWidget.addTab(self.container, 'Objects')

        # Connections do things!
        self.tileDisplay.clicked.connect(self.paintFormat)
        self.tileDisplay.mouseMoved.connect(self.updateInfo)
        self.objectList.clicked.connect(self.tileWidget.setObject)
        
        # Layout
        frameLayout.addWidget(self.infoDisplay, 0, 0, 1, 1)
        frameLayout.addWidget(self.tileDisplay, 1, 0)
        frameLayout.addWidget(self.tabWidget, 0, 1, 2, 1)
        self.setCentralWidget(frame)


    def updateInfo(self, x, y):
        
        index = [self.tileDisplay.indexAt(QtCore.QPoint(x, y))]
        curTile = Tileset.tiles[index[0].row()]
        info = self.infoDisplay
        palette = self.paletteWidget
        
        propertyList = []
        propertyText = ''
        coreType = 0
        
        if curTile.byte3 & 32:
            coreType = 1
        elif curTile.byte3 & 64:
            coreType = 2
        elif curTile.byte2 & 8:
            coreType = 3
        elif curTile.byte3 & 2:
            coreType = 4
        elif curTile.byte3 & 8:
            coreType = 5
        elif curTile.byte2 & 4:
            coreType = 6
        elif curTile.byte2 & 16:
            coreType = 7
        elif curTile.byte1 & 1:
            coreType = 8
        elif 0 > curTile.byte7 > 0x23:
            coretype = 9
        elif curTile.byte5 == 4 or 5:
            coretype = 10
            
        
        if curTile.byte3 & 1:
            propertyList.append('Solid')
        if curTile.byte3 & 16:
            propertyList.append('Breakable')
        if curTile.byte2 & 128:
            propertyList.append('Pass-Through')
        if curTile.byte2 & 32:
            propertyList.append('Pass-Down')
        if curTile.byte1 & 2:
            propertyList.append('Falling')
        if curTile.byte1 & 8:
            propertyList.append('Ledge')

            
        if len(propertyList) == 0:
            propertyText = 'None'
        elif len(propertyList) == 1:
            propertyText = propertyList[0]
        else:
            propertyText = propertyList.pop(0)
            for string in propertyList:
                propertyText = propertyText + ', ' + string

        if coreType == 0:
            if curTile.byte7 == 0x23:
                parameter = palette.ParameterList[coreType][1]
            elif curTile.byte7 == 0x28:
                parameter = palette.ParameterList[coreType][2]
            elif curTile.byte7 >= 0x35:
                parameter = palette.ParameterList[coreType][curTile.byte7 - 0x32]
            else:
                parameter = palette.ParameterList[coreType][0]
        else:
            parameter = palette.ParameterList[coreType][curTile.byte7]


        info.coreImage.setPixmap(palette.coreTypes[coreType][1].pixmap(24,24))
        info.terrainImage.setPixmap(palette.terrainTypes[curTile.byte5][1].pixmap(24,24))
        info.parameterImage.setPixmap(parameter[1].pixmap(24,24))

        info.coreInfo.setText(palette.coreTypes[coreType][0])
        info.propertyInfo.setText(propertyText)
        info.terrainInfo.setText(palette.terrainTypes[curTile.byte5][0])
        info.paramInfo.setText(parameter[0])

        info.hexdata.setText('Hex Data: {0} {1} {2} {3}\n                {4} {5} {6} {7}'.format(
                                hex(curTile.byte0), hex(curTile.byte1), hex(curTile.byte2), hex(curTile.byte3),
                                hex(curTile.byte4), hex(curTile.byte5), hex(curTile.byte6), hex(curTile.byte7)))
        


    def paintFormat(self, index):
        if self.tabWidget.currentIndex() == 1:
            return
    
        curTile = Tileset.tiles[index.row()]
        palette = self.paletteWidget

        if palette.coreWidgets[8].isChecked() == 1 or palette.propertyWidgets[0].isChecked() == 1:
            solid = 1
        else:
            solid = 0
        

        curTile.byte1 = ((palette.coreWidgets[8].isChecked()) + 
                        (palette.propertyWidgets[2].isChecked() << 1) +
                        (palette.propertyWidgets[3].isChecked() << 3))
        curTile.byte2 = ((palette.coreWidgets[6].isChecked() << 2) + 
                        (palette.coreWidgets[3].isChecked() << 3) + 
                        (palette.coreWidgets[7].isChecked() << 4) + 
                        (palette.PassDown.isChecked() << 5) + 
                        (palette.PassThrough.isChecked() << 7)) 
        curTile.byte3 = ((solid) + 
                        (palette.coreWidgets[4].isChecked() << 1) + 
                        (palette.coreWidgets[5].isChecked() << 3) + 
                        (palette.propertyWidgets[1].isChecked() << 4) + 
                        (palette.coreWidgets[1].isChecked() << 5) + 
                        (palette.coreWidgets[2].isChecked() << 6))
        curTile.byte4 = 0
        if palette.coreWidgets[2].isChecked():
            curTile.byte5 = 4
        curTile.byte5 = palette.terrainType.currentIndex()
        
        if palette.coreWidgets[0].isChecked():
            params = palette.parameters.currentIndex()
            if params == 0:
                curTile.byte7 = 0
            elif params == 1:
                curTile.byte7 = 0x23
            elif params == 2:
                curTile.byte7 = 0x28
            elif params >= 3:
                curTile.byte7 = params + 0x32
        else:
            curTile.byte7 = palette.parameters.currentIndex()

        self.updateInfo(0, 0)
        self.tileDisplay.update()



#############################################################################################
####################################### Main Function #######################################


if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    app.deleteLater()