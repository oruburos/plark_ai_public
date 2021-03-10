from gym_plark.envs.plark_env import PlarkEnv

import os, subprocess, time, signal
import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

import sys
from plark_game import classes



import logging

logger = logging.getLogger(__name__)




class PlarkEnvGuidedSonobuoy(PlarkEnv):

    def __init__(self, config_file_path=None,rewards={}, verbose=False, **kwargs):
        if kwargs is None:
            kwargs = {}
        kwargs['driving_agent'] = 'pelican'


        self.rewards = []
        super(PlarkEnvGuidedSonobuoy, self).__init__(config_file_path, verbose, **kwargs)
        if self.driving_agent != 'pelican':
            raise ValueError('This environment only supports pelican')


        self.set_rewards(**rewards)
        self.game = self.env.activeGames[len(self.env.activeGames) - 1]

        self.pelican_col = self.game.pelicanPlayer.col
        self.pelican_row = self.game.pelicanPlayer.row
        self.map_width = self.game.map_width
        self.buoy_range = self.game.sonobuoy_parameters["active_range"]
        self.map_width = self.game.map_width
        self.globalSonobuoys = self.game.globalSonobuoys

        self.distance_from_plark =[]
        self.distances_from_plark = []


    def set_rewards(self, **kwargs):
        self.illegal_move_reward = kwargs.get("illegal_move_reward", 0)
        self.end_turn_reward = kwargs.get("end_turn_reward", 0)

        self.min_buoy_row = kwargs.get("min_buoy_row", 0)
        self.drop_buoy_reward = kwargs.get("drop_buoy_reward", 0)
        self.dropped_all_buoys_reward = kwargs.get("dropped_all_buoys_reward", 0)
        self.buoy_too_close_reward = kwargs.get("buoy_too_close_reward", 0)

        self.directly_over_plark_reward = kwargs.get("directly_over_plark_reward", 0)
        self.closer_to_plark_reward = kwargs.get("closer_to_plark_reward", 0)
        self.further_from_plark_reward = kwargs.get("further_from_plark_reward", 0)

        self.drop_torpedo_near_plark_reward = kwargs.get("drop_torpedo_near_plark_reward", 0)
        self.drop_torpedo_far_from_plark_reward = kwargs.get("drop_torpedo_far_from_plark_reward", 0)
        self.define_near_plark_distance = kwargs.get("define_near_plark_distance", 5)

        self.win_reward = kwargs.get("win_reward", 1)
        self.lose_reward = kwargs.get("lose_reward", -1)

        self.max_abs_reward = kwargs.get("max_abs_reward", None)

    def distance(self, x, y):
        if x >= y:
            result = x - y
        else:
            result = y - x
        return result

    def step(self, action):
        action = self.ACTION_LOOKUP[action]


        logger.info('Action:' + action)
        game = self.env.activeGames[len(self.env.activeGames) - 1]
        gameState, uioutput = game.game_step(action)

        self.status = gameState
        self.uioutput = uioutput

        reward = 0

        logger.info('State:  '+ str(gameState))
        self.new_pelican_col = game.pelicanPlayer.col
        self.new_pelican_row = game.pelicanPlayer.row

        self.new_plark_col = game.pantherPlayer.col
        self.new_plark_row = game.pantherPlayer.row

        self.distance_from_plark = np.linalg.norm(
            np.array([self.new_pelican_col, self.new_pelican_row]) -
            np.array([self.new_plark_col, self.new_plark_row])
        )

        if game.illegal_pelican_move:
            reward += self.illegal_move_reward
        else:
            if action == "end":
                reward += self.end_turn_reward

            self.globalSonobuoys = game.globalSonobuoys

            if action == 'drop_buoy' and self.new_pelican_row > self.min_buoy_row:

                reward += self.drop_buoy_reward

                current_buoy_col = self.globalSonobuoys[-1].col
                current_buoy_row = self.globalSonobuoys[-1].row

                distance_to_top = current_buoy_row + 1
                distance_to_left = current_buoy_col + 1
                distance_to_right = self.map_width - current_buoy_col
                distance_to_edges = np.array([distance_to_top,
                                              distance_to_left,
                                              distance_to_right])

                if len(self.globalSonobuoys) > 1:
                    other_buoy_cols = np.array(
                        [buoy.col for buoy in self.globalSonobuoys[:-1]]
                    )
                    distance_to_other_buoys = np.abs(other_buoy_cols - current_buoy_col)
                    distance_to_buoys_and_edges = np.append(
                        distance_to_other_buoys, distance_to_edges
                    )
                else:
                    distance_to_buoys_and_edges = distance_to_edges

                min_distance = np.min(distance_to_buoys_and_edges)
                if min_distance < self.buoy_range:
                    reward += (self.buoy_too_close_reward / self.buoy_range) * (self.buoy_range - min_distance)

            has_moved = action in ["1", "2", "3", "4", "5", "6"]
            if len(self.distances_from_plark) > 0 and has_moved:
                if self.distance_from_plark < self.distances_from_plark[-1]:
                    reward += self.closer_to_plark_reward
                elif self.distance_from_plark > self.distances_from_plark[-1]:
                    reward += self.further_from_plark_reward

            if self.distance_from_plark == 0:
                reward = reward + self.directly_over_plark_reward

        self.distances_from_plark.append(self.distance_from_plark)
        self.pelican_col = self.new_pelican_col
        self.pelican_row = self.new_pelican_row

        _info = {"turn": game.turn_count,
                 "illegal_move": game.illegal_pelican_move}

        if action == "drop_torpedo":
            if self.distance_from_plark < self.define_near_plark_distance:
                reward += self.drop_torpedo_near_plark_reward
            else:
                reward += self.drop_torpedo_far_from_plark_reward

        if self.status == "PELICANWIN":
            reward += self.win_reward
            _info["result"] = "WIN"
        elif self.status in ["ESCAPE", "BINGO", "WINCHESTER"]:
            reward += self.lose_reward
            _info["result"] = "LOSE"

        if self.max_abs_reward is not None:
            if reward > self.max_abs_reward:
                reward = self.max_abs_reward
            if reward < -self.max_abs_reward:
                reward = -self.max_abs_reward

        done = False

        if self.status in ["PELICANWIN", "ESCAPE", "BINGO", "WINCHESTER"]:
            done = True
            total_sonobuoys = game.pelican_parameters["default_sonobuoys"]
            if len(self.globalSonobuoys) == total_sonobuoys:
                reward += self.dropped_all_buoys_reward
            if self.verbose:
                logger.info("GAME STATE IS " + self.status)

        ob = self._observation()
        self.rewards.append(reward)

        return ob, reward, done, _info


    def get_episode_rewards(self):
        return self.rewards
'''
    def step(self, action):
        #logger.info('Action:' + str(action))
        action = self.ACTION_LOOKUP[action]
        #if self.verbose:
        logger.info('Action:' + action)
        gameState, uioutput = self.env.activeGames[len(self.env.activeGames) - 1].game_step(action)
        self.status = gameState
        self.uioutput = uioutput

        #logger.info('State:  '+ str(gameState))
        self.globalSonobuoys = self.env.activeGames[len(self.env.activeGames) - 1].globalSonobuoys

        distance_from_plark = np.linalg.norm(
            np.array([self.new_pelican_col, self.new_pelican_row]) -
            np.array([self.new_plark_col, self.new_plark_row])
        )

        reward = 0
        self.new_pelican_col = self.env.activeGames[len(self.env.activeGames) - 1].pelicanPlayer.col
        self.new_pelican_row = self.env.activeGames[len(self.env.activeGames) - 1].pelicanPlayer.row

        self.plark_col = self.env.activeGames[len(self.env.activeGames) - 1].pantherPlayer.col
        self.plark_row = self.env.activeGames[len(self.env.activeGames) - 1].pantherPlayer.row

        if self.status == "PELICANWIN":
            reward = reward + 1.0

        ## Reward for being directly over the plark
        if self.new_pelican_col == self.plark_col:
            reward = reward + .6
        if self.new_pelican_row == self.plark_row:
            reward = reward + .6

        ## Reward for being closer to the plark
        if self.distance(self.new_pelican_col, self.plark_col) < self.distance(self.pelican_col, self.plark_col):
            reward = reward + .4
        else:
            ## Punish for being further from the plark
            reward = reward - .6
        if self.distance(self.new_pelican_row, self.plark_row) < self.distance(self.pelican_row, self.plark_row):
            reward = reward + .4
        else:
            ## Punish for being further from the plark
            reward = reward - .6

        if reward > 1:
            reward = 1
        if reward < -1:
            reward = -1

        if action == 'drop_buoy':
            reward = reward +.03
            logger.info('SB dropped *************************' )


        if action == 'drop_torpedo':
            reward = reward -.25
            logger.info('Torpedo dropped *************************' )

        if len(self.globalSonobuoys) > 1:
             sonobuoy = self.globalSonobuoys[-1]
             sbs_in_range = self.env.activeGames[len(self.env.activeGames) - 1].gameBoard.searchRadius(sonobuoy.col,
                                                                                                       sonobuoy.row,
                                                                                                       sonobuoy.range * 1.5,
                                                                                                       "SONOBUOY")
             logger.info('Torpedo REWARDS *************************')
             sbs_in_range.remove(sonobuoy)  # remove itself from search results

             numSB = len(sbs_in_range)
             if numSB > 0:
                 logger.info('Torpedos info *************************')
                 reward = reward - (numSB*0.02)


        self.pelican_col = self.new_pelican_col
        self.pelican_row = self.new_pelican_row

        ob = self._observation()

        self.status = gameState

        logger.info('Status Observation:' + str(self.status))
        logger.info('Size Observation:' + str(len(ob)))

        done = False
        _info = {}

        _info['status'] = self.status
        #_info= self.status
        logger.info('INFO :' + str(_info))


        done = False
        if self.status == "PELICANWIN" or self.status == "BINGO" or self.status == "WINCHESTER" or self.status == "ESCAPE":
            done = True
            if self.verbose:
                logger.info("GAME STATE IS " + self.status)
            if self.status in ["ESCAPE", "BINGO", "WINCHESTER"]:
                reward = -1

        #
        # action = self.ACTION_LOOKUP[action]
        # if self.verbose:
        #     logger.info('Action:' + action)
        # gameState, uioutput = self.env.activeGames[len(self.env.activeGames) - 1].game_step(action)
        #
        # self.status = gameState
        # self.uioutput = uioutput
        #
        # reward = 0
        # self.globalSonobuoys = self.env.activeGames[len(self.env.activeGames) - 1].globalSonobuoys
        #
        # ## Reward for droping a sonobuoy
        # if action == 'drop_buoy':
        #     reward = 1.00
        #
        # if len(self.globalSonobuoys) > 1:
        #     sonobuoy = self.globalSonobuoys[-1]
        #     sbs_in_range = self.env.activeGames[len(self.env.activeGames) - 1].gameBoard.searchRadius(sonobuoy.col,
        #                                                                                               sonobuoy.row,
        #                                                                                               sonobuoy.range,
        #                                                                                               "SONOBUOY")
        #     sbs_in_range.remove(sonobuoy)  # remove itself from search results
        #
        #     if len(sbs_in_range) > 0:
        #         reward = reward - 0.5
        #
        # if reward > 1:
        #     reward = 1
        # if reward < -1:
        #     reward = -1
        #
        # ob = self._observation()
        #
        #
        #
        #
        #
        # action = self.ACTION_LOOKUP[action]
        # if self.verbose:
        #     logger.info('Action:' + action)
        # gameState, uioutput = self.env.activeGames[len(self.env.activeGames) - 1].game_step(action)
        # self.status = gameState
        # self.uioutput = uioutput
        #
        # reward = 0
        # self.new_pelican_col = self.env.activeGames[len(self.env.activeGames) - 1].pelicanPlayer.col
        # self.new_pelican_row = self.env.activeGames[len(self.env.activeGames) - 1].pelicanPlayer.row
        #
        # if self.new_pelican_col == 0:
        #     reward = reward + .5
        # if self.new_pelican_row == 0:
        #     reward = reward + .5
        # if self.new_pelican_col < self.pelican_col:
        #     reward = reward + .1
        # if self.new_pelican_row < self.pelican_row:
        #     reward = reward + .1
        # if self.new_pelican_col > self.pelican_col:
        #     reward = reward - .3
        # if self.new_pelican_row > self.pelican_row:
        #     reward = reward - .3
        #
        # if reward > 1:
        #     reward = 1
        # if reward < -1:
        #     reward = -1
        #
        # self.pelican_col = self.new_pelican_col
        # self.pelican_row = self.new_pelican_row
        #
        # ob = self._observation()

        if game.illegal_pelican_move:
            reward += self.illegal_move_reward
        else:
            if action == "end":
                reward += self.end_turn_reward

            self.globalSonobuoys = game.globalSonobuoys

            if action == 'drop_buoy' and self.new_pelican_row > self.min_buoy_row:

                reward += self.drop_buoy_reward

                current_buoy_col = self.globalSonobuoys[-1].col
                current_buoy_row = self.globalSonobuoys[-1].row

                distance_to_top = current_buoy_row + 1
                distance_to_left = current_buoy_col + 1
                distance_to_right = self.map_width - current_buoy_col
                distance_to_edges = np.array([distance_to_top,
                                              distance_to_left,
                                              distance_to_right])

                if len(self.globalSonobuoys) > 1:
                    other_buoy_cols = np.array(
                        [buoy.col for buoy in self.globalSonobuoys[:-1]]
                    )
                    distance_to_other_buoys = np.abs(other_buoy_cols - current_buoy_col)
                    distance_to_buoys_and_edges = np.append(
                        distance_to_other_buoys, distance_to_edges
                    )
                else:
                    distance_to_buoys_and_edges = distance_to_edges

                min_distance = np.min(distance_to_buoys_and_edges)
                if min_distance < self.buoy_range:
                    reward += (self.buoy_too_close_reward / self.buoy_range) * (self.buoy_range - min_distance)

            has_moved = action in ["1", "2", "3", "4", "5", "6"]
            if len(self.distances_from_plark) > 0 and has_moved:
                if distance_from_plark < self.distances_from_plark[-1]:
                    reward += self.closer_to_plark_reward
                elif distance_from_plark > self.distances_from_plark[-1]:
                    reward += self.further_from_plark_reward

            if distance_from_plark == 0:
                reward = reward + self.directly_over_plark_reward

        self.distances_from_plark.append(distance_from_plark)
        self.pelican_col = self.new_pelican_col
        self.pelican_row = self.new_pelican_row

        _info = {"turn": game.turn_count,
                 "illegal_move": game.illegal_pelican_move}

        if action == "drop_torpedo":
            if distance_from_plark < self.define_near_plark_distance:
                reward += self.drop_torpedo_near_plark_reward
            else:
                reward += self.drop_torpedo_far_from_plark_reward

        if self.status == "PELICANWIN":
            reward += self.win_reward
            _info["result"] = "WIN"
        elif self.status in ["ESCAPE", "BINGO", "WINCHESTER"]:
            reward += self.lose_reward
            _info["result"] = "LOSE"

        if self.max_abs_reward is not None:
            if reward > self.max_abs_reward:
                reward = self.max_abs_reward
            if reward < -self.max_abs_reward:
                reward = -self.max_abs_reward

        done = False

        if self.status in ["PELICANWIN", "ESCAPE", "BINGO", "WINCHESTER"]:
            done = True
            total_sonobuoys = game.pelican_parameters["default_sonobuoys"]
            if len(self.globalSonobuoys) == total_sonobuoys:
                reward += self.dropped_all_buoys_reward
            if self.verbose:
                logger.info("GAME STATE IS " + self.status)


        done = False

        if self.status in ["PELICANWIN", "ESCAPE", "BINGO", "WINCHESTER"]:
            done = True
            if self.verbose:
                logger.info("GAME STATE IS step 1 IS: " + self.status)
        if self.new_pelican_col == 0 and self.new_pelican_row == 0:
            done = True
            if self.verbose:
                logger.info("GAME STATE step 2 IS: " + self.status)




        return ob, reward, done, _info
'''