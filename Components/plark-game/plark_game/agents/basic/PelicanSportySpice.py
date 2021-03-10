from plark_game.classes.pelicanAgent import Pelican_Agent
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



STEPS_TO_DROP_SB = 10
RANGE_TO_SB_THRESH = 0.03


def steps_to_drop_SB(n):
    if n % STEPS_TO_DROP_SB == STEPS_TO_DROP_SB - 1:
        return True
    else:
        return False


class Pelican_sportyspice(Pelican_Agent):
    def __init__(self):
        #         self.moves_taken = 0
        self.drop_t_x = -50
        self.drop_t_y = -50
        self.steps = 0


        logger.info('INIT SportySpice')
   # def get_name(self):
    #    pass

    def getAction(self, obs):

        x = obs[4]
        y = obs[5]
        logger.info('get position in pelican MY AGENT {} {}'.format( x, y))

        #in the opening, the logic is going down
        #in the midgame, the logic is expand the sonobuoys
        #in the ending, unleash fire = release all remaining torpedos
        #how do you define each pelican phase? opening is 1/4 play time OR reaching .5 of y ratio
        # midgame is  from .25 to .75 play time


        currentTurn = obs[2]
        maxTurn = obs[3]
        logger.info('get turns in game in pelican MY AGENT {} {}'.format( currentTurn, maxTurn) )
        playtime = currentTurn/maxTurn


        action = 3  # D

        if y > 0.35 and y < 0.5 and x > 0.45:
            action = 2  # DR
            self.steps += 1
            #             print('DR', x,y)
            if steps_to_drop_SB(self.steps):
                action = 6
                self.steps = 0

        if y > 0.5 and x > 0.45:
            self.steps += 1
            #             print('DL', x, y)
            action = 4  # DL
            if steps_to_drop_SB(self.steps):
                self.steps = 0
                action = 6

        if y > 0.5 and x < 0.45:
            #             print('UL', x,y)
            self.steps += 1
            action = 5  # UL
            if steps_to_drop_SB(self.steps):
                self.steps = 0
                action = 6

        if y > 0.35 and y < 0.5 and x < 0.45:
            #             print('UR',x,y)
            self.steps += 1
            action = 1  # UR
            if steps_to_drop_SB(self.steps):
                self.steps = 0
                ation = 6

        # if hot bouy, drop torpedo
        #         print (obs[9],obs[10],obs[11],obs[12],obs[13],obs[14])
        for i in range(11, 39, 3):
            if obs[i] == 0:
                pass
            #                 print('not hot')
            else:
                #                 print('hot')
                self.drop_t_x = obs[i - 2]
                self.drop_t_y = obs[i - 1]

        # move to location x,y (if multiple hot SB, then the latset one should be here)
        #         print(self.drop_t_x, self.drop_t_y)

        # if current x > drop x ... move left; if current y > drop y ... move up
        # if x, y are w/ in a small degree, drop torpedo

        if self.drop_t_x > -45 and self.drop_t_y > -45:

            if y > self.drop_t_y and abs(y - self.drop_t_y) > RANGE_TO_SB_THRESH:  # if different is big enough
                action = 0
            #                 print('move U')
            elif y < self.drop_t_y and abs(y - self.drop_t_y) > RANGE_TO_SB_THRESH:
                action = 3
            #                 print('move D')
            if x > self.drop_t_x and abs(x - self.drop_t_x) > RANGE_TO_SB_THRESH:
                action = 5
            #                 print('move L')
            elif x < self.drop_t_x and abs(x - self.drop_t_x) > RANGE_TO_SB_THRESH:
                action = 1
            #                 print('move R')

            if abs(x - self.drop_t_x) <= RANGE_TO_SB_THRESH and abs(
                    y - self.drop_t_y) <= RANGE_TO_SB_THRESH:  # close enough to hot SB, drop torpedo
                action = 7
        #                 print(x, self.drop_t_x, y, self.drop_t_y)
        #                 print(abs(x - self.drop_t_x), abs(y - self.drop_t_y))
        #                 print('drop')

        return action
#         return self.action_lookup(action)