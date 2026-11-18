import os 
import pygame
import random
import math
import numpy as np
import threading
pygame.init()
pygame.display.set_caption("A Platformer Game")
WIDTH,HEIGHT=1000,500
FPS=60
VEL=5
SIZEFACTOR=2
RAN=True
COLORS=["Yellow"]
ANISPEED=3
WIN=pygame.display.set_mode((WIDTH,HEIGHT))
file=os.path.abspath(__file__).split("\\")
file=file[0:len(file)-1]
fpath="\\".join(file)
PATH=os.path.join(fpath,"assets")
BLOCKSIZE=48
BLOCK=2
BLOCK*=64 #Blocks at Differ of 64
BLOCKIMG=None

def genframeVal():
    num=0
    while True:
        yield num
        num+=1
def abimg(img):
    _,_,width,height=img.get_rect()
    return (img,width,height)

def flipimg(imgs):
    fimgs=[]
    for img in imgs:
        fimgs.append(pygame.transform.flip(img,1,0))
    return fimgs

def loadSpriteSheets(dir,dir2,width,height,SIZEFACTOR=2):
    images=[]
    fopath=os.path.join(PATH,dir)
    if dir2:
        cpath=os.path.join(fopath,dir2)
    else:
        cpath=fopath
    for file in os.listdir(cpath):
        if os.path.isfile(os.path.join(cpath,file)):
            fpath=os.path.join(cpath,file)
            images.append(fpath)
    all_anims={}
    all_masks={}
    for image in images:
        sheet=pygame.image.load(image)
        anims=[]
        for i in range(sheet.get_width()//width):
            surface=pygame.Surface((width,height),pygame.SRCALPHA,32)
            rect=pygame.Rect(i*width,0,width,height)
            surface.blit(sheet,(0,0),rect)
            # r=surface.get_bounding_rect() 
            # surface=surface.subsurface(r).copy()
            anims.append(pygame.transform.scale_by(surface,SIZEFACTOR))
        name = os.path.splitext(os.path.basename(image))[0]
        right_anims = anims
        left_anims = flipimg(anims)
        all_anims[name + "_right"] = anims
        all_anims[name + "_left"] = flipimg(anims)
        all_masks[name + "_right"] = [pygame.mask.from_surface(s) for s in right_anims]
        all_masks[name + "_left"] = [pygame.mask.from_surface(s) for s in left_anims]
        
    return all_anims,all_masks

def handleGravity(obj):
    GRAVITY = obj.grav
    TV = 10
    
    if not obj.onPlatform:
        if not obj.onground:
            obj.fall_vel += GRAVITY
            if obj.fall_vel > TV:
                obj.fall_vel = TV
            obj.rect.y += obj.fall_vel
        else:
            obj.fall_vel = 0
        if obj.rect.y >= HEIGHT - obj.rect.height and not obj.onPlatform:
            obj.rect.y = HEIGHT - obj.rect.height
            obj.onground = True
        else:
            obj.onground = False
        obj.y_vel = obj.fall_vel
            
class Tag(pygame.sprite.Sprite):
    def __init__(self,P1,P2):
        super().__init__()
        img=pygame.image.load(os.path.join(PATH,"tag.png")).convert_alpha()
        r=img.get_bounding_rect()
        self.sprite=img.subsurface(r).copy()
        self.sprite=pygame.transform.scale_by(self.sprite,3)
        self.rect=self.sprite.get_rect(center=(0,0))
        self.P1=P1
        self.P2=P2
    def follow(self):
        self.rect.x=self.tagged.rect.x+self.tagged.rect.width//3
        self.rect.y=self.tagged.rect.y-self.tagged.rect.height//4
    def loop(self):
        self.tagged=self.P1 if self.P1.tagged else self.P2
        self.follow()
class Player(pygame.sprite.Sprite):
    fr2=genframeVal()
    def __init__(self,x,y,vel,grav,jump,player,Pnum):
        super().__init__()
        self.pnum=Pnum
        self.sprites,self.masks=loadSpriteSheets("MainCharacters",player,32,32)
        self.masksheet=self.masks["idle_right"]
        self.mask=self.masksheet[0]
        exsprite=pygame.Surface.get_rect(self.sprites["idle_right"][0])
        self.rect=pygame.Rect(x,y,exsprite.width,exsprite.height+5).scale_by(0.75)
        self.direction="right" if Pnum==1 else "left"
        self.vel=vel
        self.jump=jump
        self.grav=grav
        self.fall_vel=0
        self.fall=0
        self.spritetoDraw=self.sprites["idle_right"][0]
        self.i=0
        self.frcount=genframeVal()
        self.spritesheet="idle"
        self.y_vel=0
        self.x_vel=0
        self.onground=True
        self.onPlatform=False
        
        self.jumpcount=0
        self.state="idle_"
        
        self.tagged=False
    def handlemove(self):
        if self.pnum==1:
            right,left=pygame.K_RIGHT,pygame.K_LEFT
        else:
            right,left=pygame.K_d,pygame.K_a
        keys=pygame.key.get_pressed()
        if keys[right] and self.rect.x<(WIDTH-self.rect.width):
            self.x_vel=self.vel
            if self.direction!="right":
                self.direction="right"
            self.rect.x=self.rect.x+self.vel
        elif keys[left] and self.rect.x>0:
            self.x_vel=-self.vel
            if self.direction!="left":
                self.direction="left"
            self.rect.x=self.rect.x-self.vel
        else:
            self.x_vel=0
            
    def handleJump(self):
        if self.pnum==1:
            up=pygame.K_UP
        else:
            up=pygame.K_w
        keys = pygame.key.get_pressed()
        if keys[up] and self.onground:
            self.jumpcount=1
            self.state="jump_"
            self.fall_vel = -self.jump
            self.y_vel = self.fall_vel
            self.onground = False
            self.onPlatform=False
        if keys[pygame.K_SPACE] and not self.onground and self.jumpcount==1:
            self.jumpcount=2
            self.state="double_jump_"
            self.fall_vel = -self.jump
            self.y_vel = self.fall_vel
    
    def handleAnims(self):
        prev=self.state
        if self.x_vel!=0:
            self.state="run_"
        elif self.y_vel>0:
            self.state="fall_"
        elif self.y_vel<0:
            if self.jumpcount==1:
                self.state="jump_"
            elif self.jumpcount==2:
                self.state="double_jump_"
        else:
            self.state="idle_"
            
        if self.state != prev:
            self.i = 0
        key=self.state+self.direction
        self.spritesheet=self.sprites[key]
        self.masksheet=self.masks[key]
        
    def handleDraw(self):
        if self.i >= len(self.spritesheet):
                self.i = 0
        if (next(self.frcount) + 3) % ANISPEED == 0:
            self.spritetoDraw = self.spritesheet[self.i]
            self.mask = self.masksheet[self.i]
            self.i += 1
    
    def land(self):
        self.onground=True
        # self.onPlatform = True
        self.fall_vel=0
        self.y_vel=0
        
    def hitHead(self):
        self.fall_vel = 0
    
    @staticmethod
    def handle_vertical_coll(self,objs):
        # self.onPlatform = False
        for obj in objs:
            if self.rect.colliderect(obj.rect):
                if self.y_vel>0:
                    self.rect.bottom=obj.rect.top
                    self.land()
                elif self.y_vel<0:
                    self.rect.top=obj.rect.bottom
                    self.hitHead()
        # if self.rect.y<HEIGHT-75 and not self.onground:
        #     self.onPlatform=False
        # elif not sel:
        #     self.onPlatform=False
        #     self.onground=True
    # @staticmethod
    def handle_horizontal_coll(self, objs):
        for obj in objs:
            if self.rect.colliderect(obj.rect):
                if self.x_vel > 0:
                    self.rect.right = obj.rect.left
                elif self.x_vel < 0:
                    self.rect.left = obj.rect.right
    # def handle_horizontal_coll(self, objs):
    #     self.rect.x+=self.x_vel
    #     collidedobjs = None
    #     for obj in objs:
    #         if pygame.sprite.collide_mask(obj,self) and not self.onground:
    #             collidedobjs=obj
    #     # if self.rect.colliderect(player2.rect):
    #     #     if pygame.sprite.collide_mask(self,player2):
    #     #         collidedobjs=player2
    #     self.rect.x-=self.x_vel
    #     self.rect.x-=self.x_vel if collidedobjs else 0
        
    def loop(self,objs,platforms):
        self.playerprev=self.rect
        self.handlemove()
        self.handle_horizontal_coll(platforms)
        self.handleJump()
        handleGravity(self)
        self.handle_vertical_coll(self,objs)
        self.handleAnims()
        self.handleDraw()

def settingupVars(ran=False,colors=["Blue"]):
    global dts,twh
    tpath=os.path.join(PATH,"Background")
    if ran==True:
        dts=[]
        for tile in os.listdir(tpath):
            dts.append(os.path.join(tpath,tile))
        twh=[]
        for i in dts:
            img=pygame.image.load(i)
            s=abimg(img)
            twh.append(s)
    else:
        twh=[]
        for i in colors:
            path=os.path.join(tpath,i+".png")
            img=pygame.image.load(path).convert_alpha()
            s=abimg(img)
            twh.append(s)
settingupVars(RAN,COLORS)

def load_block(size,blocksize):
    path=os.path.join(PATH,"Terrain","Terrain.png")
    img=pygame.image.load(path).convert_alpha()
    surface=pygame.Surface((size,size),pygame.SRCALPHA,32)
    rect=pygame.Rect(96,BLOCK,size,size)
    surface.blit(img,(0,0),rect)
    return pygame.transform.scale(surface,(blocksize,blocksize))

def create_platforms(spec):
    platforms = []
    for start_x, y, count in spec:
        for i in range(count):
            platforms.append(Genblock(start_x + i * BLOCKSIZE, y, BLOCKSIZE, BLOCKSIZE))
    return platforms


class Object(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,name=None):
        super().__init__()
        self.rect=pygame.Rect(x,y,width,height)
        self.image=pygame.Surface((width,height),pygame.SRCALPHA)
        self.width=width
        self.heigh=height
        self.name=name

class Genblock(Object):
    def __init__(self,x,y,width,height):
        super().__init__(x,y,width,height)
        block=load_block(48,BLOCKSIZE)
        self.image.blit(block,(0,0))
        self.mask=pygame.mask.from_surface(self.image)
    def Draw(self):
        WIN.blit(self.image,self.rect)

def getBgPos(twh):
    tpos=[]
    for i in range(WIDTH//2+1):
        for j in range(HEIGHT//2+1):
            randtile=random.choice(twh)
            pos=(i*twh[0][1],j*twh[0][2])
            tpos.append((pos,randtile[0]))
    return tpos


        
def draw(bg,objs,P1,P2,tag):
    WIN.blit(bg,(0,0))
    for obj in objs:
        obj.Draw()
    pygame.draw.rect(WIN,(0,0,0),P1.rect)
    pygame.draw.rect(WIN,(0,0,0),P2.rect)
    WIN.blit(tag.sprite,tag.rect)
    WIN.blit(P1.spritetoDraw, P1.spritetoDraw.get_rect(midbottom=P1.rect.midbottom))
    WIN.blit(P2.spritetoDraw, P2.spritetoDraw.get_rect(midbottom=P2.rect.midbottom))
    pygame.display.update()
    
def cachebg(tile):
    img=pygame.Surface((WIDTH,HEIGHT))
    for i in tile:
        img.blit(i[1],i[0])
    return img

def main():
    player1=Player(64,0,VEL,0.5,12,"VirtualGuy",2)
    player2=Player(WIDTH-128,0,VEL,0.5,12,"MaskDude",1)
    floor=[Genblock(i*BLOCKSIZE,HEIGHT-BLOCKSIZE//2,BLOCKSIZE,BLOCKSIZE) for i in range(-WIDTH//BLOCKSIZE,WIDTH*2//BLOCKSIZE)]
    platform=[(120, 340, 4),(680, 340, 4),(404, 230, 4),(160, 150, 3),(696, 150, 3)]
    platforms=create_platforms(platform)
    blocks=floor+platforms
    tile=getBgPos(twh)
    clock=pygame.time.Clock()
    run=True
    img=cachebg(tile)
    tagStart=[True,False]
    random.shuffle(tagStart)
    player1.tagged=tagStart[0]
    player2.tagged=tagStart[1]
    TagC=0
    tag=Tag(player1,player2)
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run=False
        player1.loop(blocks,platforms)
        player2.loop(blocks,platforms)
        offset=(player2.rect.x-player1.rect.x,player2.rect.y-player1.rect.y)
        if player1.mask.overlap(player2.mask,offset) and TagC>60:
            if player1.tagged==1:
                player2.tagged=1
                player1.tagged=0
                print("Tag By 1")
            else:
                player2.tagged=0
                player1.tagged=1
                print("Tag By 2")
            TagC=0
            
        tag.loop()
        draw(img,blocks,player1,player2,tag)
        TagC+=1
    
    pygame.quit()
    quit()
if __name__=="__main__":
    main()