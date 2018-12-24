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
                                    'Last Edit': int(datetime.datetime.now().strftime("%j")), 'Nicknames': []
                                    },
                        geometry={"type": "Point", "coordinates": coordinates, "bbox": [coordinates[0], coordinates[1], coordinates[0], coordinates[1]]})


def reset_old_tasks(taskmap):
    """Reset the tasks that are out of date in a map."""
    stops_reset = False
    for stop in taskmap:
        if not('Nicknames' in stop.properties):
            stop.properties['Nicknames'] = []
        if 'nicknames' in stop.properties:
            del stop.properties['nicknames']
        if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
            reset_task(stop)
            stops_reset = True
    return stops_reset


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
    stops_found = []
    for stop in taskmap:
        if (stop.properties['Stop Name'].title() == stop_name.title() or stop_name.lower() in stop.properties['Nicknames']):
            if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
                reset_all_tasks(taskmap)
            stops_found.append(stop)
    if len(stops_found) == 0:
        raise StopNotFound()
    elif len(stops_found) == 1:
        return stops_found[0]
    else:
        temp_num = 1
        for stop in stops_found:
            if not(stop.properties['Nicknames']):
                stop.properties['Nicknames'].append('temp' + str(temp_num))
                temp_num += 1
        raise MutlipleStopsFound(stops_found)


def set_task(stop, task):
    """Add a task to a stop, checking if the stop already has a task."""
    if stop.properties['Task'] == '':
        stop.properties['Task'] = task.quest
        stop.properties['Reward'] = task.reward
        stop.properties['Last Edit'] = int(datetime.datetime.now().strftime("%j"))
        stop.properties['Category'] = task.reward_type
    else:
        raise TaskAlreadyAssigned(stop, task)


def find_task(tasklist, task_str):
    """Find a task in the list with a given reward or quest."""
    task_str = task_str.title()
    task_not_found = True
    while task_not_found:
        for tasks in tasklist:
            if (task_str == tasks.reward.title()) or (task_str == tasks.quest.title()):
                return tasks
                task_not_found = False
        break
    if task_not_found:
        raise ValueError('Task not found')


def save_object(obj, filename):
    """Save an object using pickle."""
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def add_stop_nickname(stop,nickname):
    """Add a nickname to a stop."""
    if 'Nicknames' not in stop.properties:
        stop.properties['Nicknames'] = []
    if (len(stop.properties['Nicknames']) == 1 and stop.properties['Nicknames'][0].startswith('temp')):
        stop.properties['Nicknames'][0] = nickname.lower()
    else:
        stop.properties['Nicknames'].append(nickname.lower())


def add_task_nickname(task,nickname):
    """Add a nickname to a task."""
    task.nicknames.append(nickname)


# Classes
# Task Class
class Task():
    """Class for Pokemon Go research tasks."""

    def __init__(self, reward, quest, reward_type, shiny):
        """Initialize the task object based on the given inputs."""
        self.reward = reward
        self.quest = quest
        self.reward_type = reward_type
        self.shiny = shiny
        self.nicknames = []


# Custom Exceptions
class PokemapException(Exception):
    """Base class for the module so all module exceptions can be caught together."""

    def __init__(self):
        """Add default message."""
        self.message = 'No error message set, contact maintainer'


class TaskAlreadyAssigned(PokemapException):
    """Exception for trying to assign a new task to a stop that already has one."""

    def __init__(self, stop=None, task=None):
        """Add message based on context of error."""
        if (stop is None):
            msg = "Failed to assign task as stop"
        elif (task is None):
            msg = "Failed to assign task to " + stop.properties['Stop Name'] + " as it already had task " + stop.properties['Task']
        else:
            msg = "Failed to assign " + task.reward + " to " + stop.properties['Stop Name'] + " as it already had task " + stop.properties['Task']
        self.message = msg


class MutlipleStopsFound(PokemapException):
    """Exception for when multiple stops are found using the same stop search query."""

    def __init__(self, stops=None):
        """Add message based on context of error."""
        msg = "Multiple stops found with this name. Use stop nicknames to prevent this. Stops without nicknames have been given temporary nicknames, please add unique nicknames now."
        if not(stops is None):
            msg += ' Nicknames for these stops include: '
            for stop in stops:
                msg += stop.properties['Nicknames'][0] + ', '
            msg = msg[:-2] + '.'
        self.message = msg


class StopNotFound(PokemapException):
    """Exception for when stop not found with the given search string."""

    def __init__(self):
        """Add message based on context of error."""
        self.message = "No stop found with the given string."
