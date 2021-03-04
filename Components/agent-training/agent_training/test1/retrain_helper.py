import json
import numpy as np
import sys

sys.path.append('/Components/utils')
from domain_parameters import domain_parameter_ranges, compute_start_positions, create_param_instance
from domain_parameters_json import create_game_config_json





def config_to_string(parameter_instance):
	param_string = ""
	#for param in parameter_instance:
	#	param_string = param_string + param + "_"

	param_string = param_string + str(parameter_instance["map_width"]) + "_"
	param_string = param_string + str(parameter_instance["map_height"]) + "_"
	param_string = param_string + str(parameter_instance["max_turns"]) + "_"
	param_string = param_string + str(parameter_instance["move_limit_panther"]) + "_"
	param_string = param_string + str(parameter_instance["move_limit_pelican"]) + "_"
	param_string = param_string + str(parameter_instance["default_torpedos"]) + "_"
	param_string = param_string + str(parameter_instance["default_sonobuoys"]) + "_"
	param_string = param_string + str(parameter_instance["turn_limit"]) + "_"
	param_string = param_string + str(parameter_instance["speed"]) + "_"
	param_string = param_string + str(parameter_instance["search_range"]) + "_"
	param_string = param_string + str(parameter_instance["active_range"]) + "_"
	param_string = param_string + str(parameter_instance["start_col_panther"]) + "_"
	param_string = param_string + str(parameter_instance["start_row_panther"]) + "_"
	param_string = param_string + str(parameter_instance["start_col_pelican"]) + "_"
	param_string = param_string + str(parameter_instance["start_row_pelican"])
	return param_string



def get_config_from_string(config_string):
	splitted = config_string.split("_")
	config_list = []
	for element in splitted:
		config_list.append( int(element) )

	param_instance = create_param_instance(np.asarray(config_list))
	return param_instance


def get_normalised_coordinates(param_instance):
	#if len(domain_parameter_ranges["start_col_pelican"]) == 0:
	compute_start_positions(param_instance["map_width"], param_instance["map_height"])

	normed_param_instance = {}

	for key,value in param_instance.items():
		lower_bound = domain_parameter_ranges[key][0]
		upper_bound = domain_parameter_ranges[key][-1]
		normed_value = (value - lower_bound) / (upper_bound - lower_bound)
		normed_param_instance[key] = normed_value

		# Just in case I'm stupid...
		#if normed_value > 1.0:
		#	normed_value = 1.0
		#if normed_value < 0.0:
		#	normed_value = 0.0

	return normed_param_instance


def get_euclidean_distance(normed_coords1, normed_coords2):

	distance = 0.0
	for key,value in normed_coords1.items():
		delta = value - normed_coords2[key]
		distance = distance + delta**2

	return np.sqrt(distance)




def dump_json_config_file(param_instance, filepath):

    game_config = create_game_config_json(param_instance)

    with open(filepath, 'w') as outfile:
        json.dump(game_config, outfile, indent=4)






#### Really unncessary as we can just create param dict directly, but just in case.
def select_domain(map_width=None,
					map_height=None,
					max_turns=None,
					move_limit_panther=None,
					move_limit_pelican=None,
					default_torpedos=None,
					default_sonobuoys=None,
					turn_limit=None,
					speed=None,
					search_range=None,
					active_range=None,
					start_col_panther=None,
					start_row_panther=None,
					start_col_pelican=None,
					start_row_pelican=None):
	list_params = [map_width, map_height, max_turns,
					 move_limit_panther, move_limit_pelican,
					 default_torpedos, default_sonobuoys,
					 turn_limit, speed, search_range,
					 active_range, start_col_panther,
					 start_row_panther, start_col_pelican,
					 start_row_pelican]

	param_instance = create_param_instance(np.asarray(list_params))
	return param_instance
