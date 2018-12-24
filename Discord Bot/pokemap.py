"""This module implements the functions and classes for making maps of research tasks in pokemon go."""

import datetime
import pickle


def add_stop(taskmap, coordinates, name):
    """Add a stop to a given map.

    Args:
        taskap (pygeoj map): map to add the stop to.
        coordinates (tuple): location of the stop in [longitude, latitude].
        name (str)- name of the stop to be added.
    Returns:
        none

    """
    taskmap.add_feature(properties={'marker-size': 'medium', 'marker-symbol': '', 'marker-color': '#808080', 'Stop Name': name, 'Task': '', 'Reward': '',
                                    'Last Edit': int(datetime.datetime.now().strftime("%j")), 'nicknames': []
                                    },
                        geometry={"type": "Point", "coordinates": coordinates, "bbox": [coordinates[0], coordinates[1], coordinates[0], coordinates[1]]})


def reset_old_tasks(taskmap):
    """Reset the tasks that are out of date in a map."""
    for stop in taskmap:
        if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
            reset_task(stop)


def reset_task(stop):
    """Reset the task on a stop."""
    stop.properties['Task'] = ''
    stop.properties['Reward'] = ''
    stop.properties['marker-color'] = '#808080'
    stop.properties['Last Edit'] = int(datetime.datetime.now().strftime("%j"))


def reset_all_tasks(taskmap):
    """Reset all the stops in a map."""
    backup_name = datetime.datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_task_backup.json'
    taskmap.save(backup_name)
    for stop in taskmap:
        reset_task(stop)


def find_stop(taskmap, stop_name):
    """Find a stop in a given map by its name."""
    stop_not_found = True
    while stop_not_found:
        for stop in taskmap:
            if stop.properties['Stop Name'] == stop_name:
                if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
                    reset_task(stop)
                return stop
                stop_not_found = False
        break
    if stop_not_found:
        raise ValueError('Stop name not found')


def set_task(stop, task):
    """Add a task to a stop, checking if the stop already has a task."""
    if stop.properties['Task'] == '':
        stop.properties['Task'] = task.quest
        stop.properties['Reward'] = task.reward
        stop.properties['Last Edit'] = int(datetime.datetime.now().strftime("%j"))
        if task.reward_type == 'Encounter':
            if task.shiny:
                stop.properties['marker-color'] = '#ffff00'
            else:
                stop.properties['marker-color'] = '#008000'
        elif task.reward_type == 'Stardust':
            stop.properties['marker-color'] = '#ff00ff'
        elif task.reward_type == 'Item':
            stop.properties['marker-color'] = '#0000ff'
        elif task.reward_type == 'Rare Candy':
            stop.properties['marker-color'] = '#ff8000'
    else:
        raise ValueError('Task Already Set')


class Task:
    """Class for Pokemon Go research tasks."""

    def __init__(self, reward, quest, reward_type, shiny):
        """Initialize the task object based on the given inputs."""
        self.reward = reward
        self.quest = quest
        self.reward_type = reward_type
        self.shiny = shiny


def find_task(tasklist, task_str):
    """Find a task in the list with a given reward or quest."""
    task_not_found = True
    while task_not_found:
        for tasks in tasklist:
            if (task_str == tasks.reward) or (task_str == tasks.quest):
                return tasks
                task_not_found = False
    if task_not_found:
        raise ValueError('Task not found')


def save_object(obj, filename):
    """Save an object using pickle."""
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
