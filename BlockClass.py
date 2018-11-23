BASE_TEXTURES = 'gfx/tex/'

BLOCKS = {
    'air': {'hotkey': 0, 'type': 'single', 'transparent': True,
            'texture': None},
    'bricks': {'hotkey': 5, 'type': 'single', 'transparent': False,
               'texture': BASE_TEXTURES + 'bricks.png'},
    'cobblestone': {'hotkey': 2, 'type': 'single', 'transparent': False,
                    'texture': BASE_TEXTURES + 'cobblestone.png'},
    'dirt': {'hotkey': 1, 'type': 'single', 'transparent': False,
             'texture': BASE_TEXTURES + 'dirt.png'},
    'glass': {'hotkey': 3, 'type': 'single', 'transparent': True,
              'texture': BASE_TEXTURES + 'glass.png'},
    'leaves': {'hotkey': 7, 'type': 'single', 'transparent': True,
               'texture': BASE_TEXTURES + 'leaves.png'},
    'planks': {'hotkey': 8, 'type': 'single', 'transparent': False,
               'texture': BASE_TEXTURES + 'planks.png'},
    'stone': {'hotkey': 9, 'type': 'single', 'transparent': False,
              'texture': BASE_TEXTURES + 'stone.png'},
    'grass': {'hotkey': 4, 'type': 'multi', 'transparent': False,
              'texture_top': BASE_TEXTURES + 'grass_top.png',
              'texture_sid': BASE_TEXTURES + 'grass_side.png',
              'texture_bot': BASE_TEXTURES + 'grass_bot.png',
              },
    'wood': {'hotkey': 6, 'type': 'multi', 'transparent': False,
             'texture_top': BASE_TEXTURES + 'wood_top.png',
             'texture_sid': BASE_TEXTURES + 'wood_side.png',
             'texture_bot': BASE_TEXTURES + 'wood_bot.png',
             },
}


class BlockClass:
    def __init__(self, my_type, the_base, x, y, z):
        self.type = my_type
        self.x, self.y, self.z = x, y, z

        if my_type == 'air':
            del self
            return

        self.the_base = the_base
        self.model = self.the_base.loader.loadModel("gfx/block")
        self.model.reparentTo(self.the_base.render)
        self.model.setPos(x, y, z)
        self.model.setTag('blockTag', '1')
        self.model.find('**/SideW').setTag('westTag', '2')
        self.model.find('**/SideN').setTag('northTag', '3')
        self.model.find('**/SideE').setTag('eastTag', '4')
        self.model.find('**/SideS').setTag('southTag', '5')
        self.model.find('**/Top').setTag('topTag', '6')
        self.model.find('**/Bottom').setTag('botTag', '7')

        if BLOCKS[my_type]['transparent']:
            self.model.setTransparency(1)

        if BLOCKS[my_type]['type'] == 'multi':
            topTexture = self.the_base.loader.loadTexture(BLOCKS[my_type]['texture_top'])
            sideTexture = self.the_base.loader.loadTexture(BLOCKS[my_type]['texture_bot'])
            botTexture = self.the_base.loader.loadTexture(BLOCKS[my_type]['texture_sid'])
            textureStage = self.model.findTextureStage('*')
            self.model.find('**/Top').setTexture(textureStage, topTexture, 1)
            self.model.find('**/Side').setTexture(textureStage, sideTexture, 1)
            self.model.find('**/Bottom').setTexture(textureStage, botTexture, 1)
        else:
            texture = self.the_base.loader.loadTexture(BLOCKS[my_type]['texture'])
            textureStage = self.model.findTextureStage('*')
            self.model.setTexture(textureStage, texture, 1)

    def cleanup(self):
        self.model.removeNode()
        del self

    def __repr__(self):
        return "%s: (%s, %s, %s)" % (self.type, self.x, self.y, self.z)
