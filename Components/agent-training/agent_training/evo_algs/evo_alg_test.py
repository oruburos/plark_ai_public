from gym_plark.envs.plark_env import PlarkEnv
from gym_plark.envs.plark_env_sparse import PlarkEnvSparse
from plark_game.agents.basic.panther_nn import PantherNN
from plark_game.agents.basic.pelican_nn import PelicanNN
from agent_training import helper

from deap import creator, base, benchmarks, cma, tools, algorithms

import numpy as np
import copy

def save_video(genome, agent, env, num_steps, file_name='evo_run.mp4'):

    agent.set_weights(genome)
    video_path = '/' + file_name
    helper.make_video_plark_env(agent, env, video_path, n_steps=num_steps)

def evaluate(genome, config_file_path, driving_agent, normalise):

    #Instantiate the env
    env = PlarkEnvSparse(config_file_path=config_file_path, image_based=False, 
                         driving_agent=driving_agent, normalise=normalise)

    num_inputs = len(env._observation())
    num_hidden_layers = 0
    neurons_per_hidden_layer = 0
    if trained_agent == 'panther':
        agent = PantherNN(num_inputs=num_inputs, num_hidden_layers=num_hidden_layers, 
                          neurons_per_hidden_layer=neurons_per_hidden_layer)  
    else:
        agent = PelicanNN(num_inputs=num_inputs, num_hidden_layers=num_hidden_layers, 
                          neurons_per_hidden_layer=neurons_per_hidden_layer)  

    agent.set_weights(genome)

    env.reset()

    max_num_steps = 200
    #max_num_steps = 10

    reward = 0
    obs = env._observation()
    for step_num in range(max_num_steps):
        #print("Step num", step_num)
        action = agent.getAction(obs)    
        obs, r, done, info = env.step(action)
        reward += r
        if done:
            break

    print("Finished at step num:", step_num)
    print("Reward:", reward)
    print("Status:", info['status'])

    #save_video(genome, agent, env, max_num_steps, file_name='evo.mp4')
    #exit()

    #if info['status'] == "PELICANWIN":
    #    save_video(genome, agent, env, max_num_steps, file_name='pelican_win.mp4')
    #if info['status'] == "ESCAPE":
    #    save_video(genome, agent, env, max_num_steps, file_name='escape.mp4')

    return [reward]

if __name__ == '__main__':

    #Env variables
    config_file_path = '/Components/plark-game/plark_game/game_config/10x10/nn/balanced_nn.json'
    #trained_agent = 'panther'
    trained_agent = 'pelican'
    normalise = True


    #Instantiate dummy env and dummy agent
    #I need to do this to ascertain the number of weights needed in the optimisation
    #procedure
    dummy_env = PlarkEnvSparse(config_file_path=config_file_path, image_based=False, 
                               driving_agent=trained_agent, normalise=normalise)

    #Neural net variables
    num_inputs = len(dummy_env._observation())
    num_hidden_layers = 0
    neurons_per_hidden_layer = 0

    if trained_agent == 'panther':
        dummy_agent = PantherNN(num_inputs=num_inputs, num_hidden_layers=num_hidden_layers, 
                                neurons_per_hidden_layer=neurons_per_hidden_layer)  
    else:
        dummy_agent = PelicanNN(num_inputs=num_inputs, num_hidden_layers=num_hidden_layers, 
                                neurons_per_hidden_layer=neurons_per_hidden_layer)  

    num_weights = dummy_agent.get_num_weights()
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("evaluate", evaluate, config_file_path=config_file_path, 
                     driving_agent=trained_agent, normalise=normalise)

    #np.random.seed(108)

    #Initial location of distribution centre
    centroid = [0.0] * num_weights
    #Initial standard deviation of the distribution
    init_sigma = 1.0
    #Number of children to produce at each generation
    #lambda_ = 20 * num_weights
    lambda_ = 100
    strategy = cma.Strategy(centroid=centroid, sigma=init_sigma, lambda_=lambda_)

    toolbox.register("generate", strategy.generate, creator.Individual)
    toolbox.register("update", strategy.update)

    parallelise = False
    if parallelise:
        import multiprocessing

        pool = multiprocessing.Pool()
        toolbox.register("map", pool.map)

    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    num_gens = 200
    population, logbook = algorithms.eaGenerateUpdate(toolbox, ngen=num_gens, 
                                                      stats=stats, halloffame=hof)

    #Save video of best agent
    save_video(hof[0], dummy_agent, num_steps=200, file_name='best_agent.mp4')
