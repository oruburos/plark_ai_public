import os
from stable_baselines import DQN, PPO2, A2C, ACKTR
from stable_baselines3 import PPO  # PyTorch Stable Baselines
from .pantherAgent import Panther_Agent
import logging
import numpy as np
from .pil_ui import PIL_UI
import gc
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Panther_Agent_Load_Agent(Panther_Agent):
    def __init__(
        self,
        filepath,
        algorithm_type,
        observation=None,
        imaged_based=True,
        in_tournament=False,
    ):
        # For the tournament, the agent won't have an observation object, even if not image_based.
        if not in_tournament:
            # Can't initialise this until we have game state
            self.pil_ui = None
            self.imaged_based = imaged_based

            if not self.imaged_based:
                if observation is not None:
                    self.observation = observation
                else:
                    raise ValueError("Observation object not passed in to load agent.")
        # load the agent
        if os.path.exists(filepath):
            self.loadAgent(filepath, algorithm_type)
            logger.info("panther agent loaded")
        else:
            raise ValueError(
                'Error loading panther agent. File : "' + filepath + '" does not exist'
            )

    def loadAgent(self, filepath, algorithm_type):
        try:
            if algorithm_type.lower() == "dqn":
                self.model = DQN.load(filepath)
            elif algorithm_type.lower() == "ppo2":
                self.model = PPO2.load(filepath)
            elif algorithm_type.lower() == "ppo":
                self.model = PPO.load(filepath)
            elif algorithm_type.lower() == "a2c":
                self.model = A2C.load(filepath)
            elif algorithm_type.lower() == "acktr":
                self.model = ACKTR.load(filepath)
        except:
            raise ValueError(
                'Error loading panther agent. File : "' + filepath + '" does not exsist'
            )

    def getAction(self, state):
        # This should be replaced by a helper method that doesn't require constructing a class instance
        if not self.pil_ui:
            self.pil_ui = PIL_UI(
                state,
                state["hexScale"],
                state["view_all"],
                state["sb_display_range"],
                state["render_width"],
                state["render_height"],
                state["sb_range"],
                state["torpedo_hunt_enabled"],
                state["torpedo_speeds"],
            )

        if self.imaged_based:
            obs = self.pil_ui.update(state)
            obs = np.array(obs, dtype=np.uint8)
        else:
            obs = self.observation.get_observation(state)

        action, _ = self.model.predict(obs, deterministic=False)
        return self.action_lookup(action)


    def getTournamentAction(self, obs, obs_normalised, domain_parameters, domain_parameters_normalised, state):
        """
        PARTICIPANTS:  the example below calls model.predict on a stable_baselines
        agent that expects the observation (a list of numbers).
        Modify this if you have an agent that expects a different input, for
        example obs_normalised, or state, or if it needs the domain_parameters.
        """
        action, _ = self.model.predict(obs, deterministic=False)
        return self.action_lookup(action)
