from pygame import *
import math
from random import random
from time import time as t
#from typing import Literal

W, H = 700, 600

window = display.set_mode((W, H))
display.set_caption('Bumbo Coin Pathfinding')
diag = math.sqrt(W**2 + H**2)
clock = time.Clock()
game = True
fps = 24
font.init()

class GameSprite(sprite.Sprite):
    def __init__(self, x, y, w, h, imagePath=None, c=(0, 0, 0)):
        super().__init__()
        if imagePath is not None:
            self.image = transform.scale(image.load(imagePath), (w, h))
        else:
            self.image = Surface((w, h))
            self.image.fill(c)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def renderSprite(self):
        window.blit(self.image, (self.rect.x, self.rect.y))

class NPC(GameSprite):
    def __init__(self, x, y, w, h, image=None, c=(0, 0, 0), speed=5):
        super().__init__(x, y, w, h, image, c)
        self.speed = speed
        self.bestPathfinderPath = None
        self.isFollowingPath = False

    def FollowPath(self):    
        #todo
        pass

    def SetEndTarget(self, x, y):
        self.endTarget = (x, y)
    
class Path():
    '''
    `Path` object used by Pathfinder.\n
    Stores:\n
    * coordinates as a list of `(x,y)` pairs;
    * average score of a path;
    * number of steps in a path.\n
    '''
    def __init__(self) -> None:
        self.coordinates = list()
        self.avgScore = 0
        self.steps = 0

    @property
    def quality(self):
        '''
        `Path`'s quality is calculated as `average_score / steps ^ 2`.
        \nThis is because it is more important to minimize the amount of steps than to maximize the proximity to the end target. 
        '''
        return self.avgScore / (self.steps ** 2)

class PathFinder(sprite.Sprite):
    def __init__(self, parent : NPC) -> None:
        super().__init__()
        self.image = Surface((5, 5))
        self.rect = self.image.get_rect()

        self.parent = parent
        self.speed = parent.speed
        self.rect.x = parent.rect.x
        self.rect.y = parent.rect.y
        self.start = (self.rect.x, self.rect.y)

        self.paths = list()
        self.time = 0

    def SetStart(self, newStart):
        self.rect.centerx, self.rect.centery = newStart
        self.parent.rect.centerx, self.parent.rect.centery = newStart
        self.start = newStart

    def SetEnd(self, newEnd):
        self.end = newEnd
        self.parent.SetEndTarget(*newEnd)

    def MoveToTarget(self, x0:float, y0:float, angle:float) -> tuple[float, float, bool]:
        '''
        Gradually move Pathfinder to a new appointed target, checking wall collisions. Total movement lenght is equal to Pathfinder's `speed`.\n
        Return:\n
        `start_x, start_y, True` if collided with a wall while moving,\n
        `end_x, end_y, False` otherwise.
        '''
        x, y = x0, y0
        for _ in range(self.speed):
            x += math.cos(angle)
            y += math.sin(angle)
            for wall in walls:
                if wall.rect.collidepoint(x, y):
                    return x0, y0, True
                
        return x, y, False

    def AddTarget(self, margin:float, rate:float) -> tuple[tuple[int, int], float]:
        '''
        Add new eligible (e.g. the one that doesn't cause Pathfinder to collide with a wall or stray away from the end target) target to PathFinder.\n
        Return:\n
        This target's coordinates as `(x, y)` pair and the final `score`.
        '''
        scores = [-1, -1]
        newAngle = random() * 2 * math.pi
        x, y = 0, 0
        while abs(scores[-1] - scores[-2]) > margin or scores[-1] == 0 or scores[-2] == -1:
            x, y, collided = self.MoveToTarget(self.rect.x, self.rect.y, newAngle)
            if collided:
                score = 0
            else:
                score = (1 - math.sqrt((x - self.end[0])**2 + (y - self.end[1])**2) / diag)
            scores.append(score)


            if scores[-1] <= scores[-2] or scores[-2] == -1:
                newAngle = random() * 2 * math.pi
            else:
                newAngle += (random() - 0.5) * math.pi * rate

        self.rect.x, self.rect.y = x, y
        return ((x, y), scores[-1])

    def FindPath(self, margin:float=1e-4, rate:float=0.45, scorePrecision:float=0.96, tries:int=4):
        '''
        GENERAL PATHFINDER ALGORITHM.\n
        Start at random angle twice. Then, closer to the end target - bigger score. Keep adjusting this angle if it gives you higher score.\n
        Wall collision sets the score to 0, so the target is reselected. This is all handled in `AddTarget`, rather than here.\n
        Add all resulting paths (`Path` objects) to `self.paths` to then choose the best one by `quality`.

        Parameters:\n
        `margin`: required margin of difference in scores before completing the step.
        `rate`: rate of angle adjustion once pathfinder finds the right angle.
        `scorePrecision`: keep going until reaching close enough `scorePrecision` from the end target.
        `tries`: how many paths to find to choose the best from.
        '''
        self.paths = list()
        start = t()

        for _ in range(tries):
            path = Path()

            new = (None, -1)
            while new[1] < scorePrecision:
                new = self.AddTarget(margin, rate)
                path.steps += 1
                path.avgScore += new[1]
                path.coordinates.append(new[0])

            path.avgScore /= path.steps
            self.paths.append(path)
            self.rect.x, self.rect.y = self.start

        end = t()
        self.time = round(end - start, 2)

    @property
    def BestPath(self):
        return max(self.paths, key=lambda x : x.quality) if len(self.paths) > 0 else None
    
    def GiveBestPathToNPC(self):
        self.parent.bestPathfinderPath = self.BestPath


npc = NPC(450, 450, 32, 32, 'npc.png', speed=15)
pf = PathFinder(npc)
coin = GameSprite(300, 50, 32, 16, 'coin.png')
walls = [
    GameSprite(100, 400, 350, 5),
    GameSprite(250, 275, 300, 5),
    GameSprite(200, 50, 5, 100),
    GameSprite(450, 100, 5, 100),
    GameSprite(350, 50, 5, 75),
]

finish = False
while game:
    window.fill((90, 155, 220))
    window.blit(font.Font(None, 20).render(
        "RMB to relocate Bumbo. LMB to relocate a coin and make Bumbo start pathfinding to it", True, (0, 0, 0)), (0, 540)
        )
    window.blit(font.Font(None, 20).render(
        "Pathfinder: margin = 0.0001, rate = 0.45, scorePrecision = 0.96. Build 4 paths and choose the best by quality", True, (0, 0, 0)), (0, 560)
        )
    if pf.BestPath is not None:
        window.blit(font.Font(None, 20).render(
            f'Best path: {pf.BestPath.steps} steps, quality = average_score / steps^2 = {pf.BestPath.quality:.6f}, total time = {pf.time}s', True, (250, 185, 5)), (0, 580)
            )
    else:
        window.blit(font.Font(None, 20).render(
            'Waiting for a Pathfinder to start...', True, (250, 185, 5)), (0, 580)
            )
    coin.renderSprite()

    for e in event.get():
        if e.type ==  QUIT:
            game = False
        elif e.type == MOUSEBUTTONDOWN:
            if e.button == BUTTON_LEFT:
                coin.rect.centerx, coin.rect.centery = e.pos
                pf.SetEnd(e.pos)
                pf.FindPath()
                pf.GiveBestPathToNPC()
            elif e.button == BUTTON_RIGHT:
                pf.SetStart(e.pos)

    for wall in walls:
        wall.renderSprite()

    # Draw pathfinder path on the screen.
    try:
        for c in npc.bestPathfinderPath.coordinates:
            draw.circle(window, (255, 0, 0), c, 2)
    except:
        pass
    
    npc.renderSprite()

    display.update()
    clock.tick(fps)




    
    
    