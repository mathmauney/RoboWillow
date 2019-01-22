"""This module implements the functions and classes for making maps of research tasks in pokemon go."""

import datetime
import pygeoj
import pickle


class Task:
    """Research task class, specified by the display name and quest."""

    def __init__(self, name, quest, shiny):
        """Initialize the task object and parse the input name into the rewards if possible."""
        self.reward = name.title()
        self.quest = quest
        self.shiny = shiny
        self.nicknames = []
        if 'Rare' in self.reward:    # Check to see what the reward type is
            self.reward_type = 'Rare Candy'
            self.nicknames.append(quest + ' RC')
        elif 'Stardust' in self.reward:
            self.reward_type = 'Stardust'
        else:
            self.reward_type = 'Encounter'
        if ' Or ' in self.reward:  # Try to parse the name into rewards
            self.rewards = self.reward.split(' Or ')
            self.reward = self.reward.replace('Or', 'or')
        elif 'Gen 1 Starter' in self.reward:
            self.rewards = ['Bulbasaur', 'Squirtle', 'Charmander']
        else:
            self.rewards = [self.reward]
        self.icon = self.rewards[0]

    def add_nickname(self, name):
        """Add a nickname to the task."""
        if not(name in self.nicknames):
            self.nicknames.append(name)

    def set_icon(self, icon):
        """Choose which reward to use as the icon"""
        icon = icon.title()
        if icon in self.rewards:
            self.icon = icon


class Tasklist:
    """Tasklist class."""

    def __init__(self):
        """Initialize the tasklist."""
        self.tasks = []

    def add_task(self, task):
        """Add a task to the tasklist"""
        self.tasks.append(task)

    def find_task(self, task_str):
        """Find a task in the list and return it."""
        task_str = task_str.title()
        task_not_found = True
        while task_not_found:
            for task in self.tasks:
                if (task_str == task.reward.title()) or (task_str == task.quest.title()) or (task_str in task.rewards):
                    return task
                    task_not_found = False
            break
        if task_not_found:
            raise TaskNotFound()

    def remove_task(self, task):
        """Remove a task from the list."""
        for i in range(len(self.tasks)):
            if self.tasks[i] is task:
                del self.tasks[i]

    def save(self, filename='tasklist.pkl'):
        """Save the tasklist."""
        with open(filename, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

    def clear(self):
        """Clear the tasklist."""
        self.tasks = []


class Stop(pygeoj.Feature):
    """Extension of the pygeoj feature class that includes more methods that are useful for pokestops."""

    def reset(self):
        """Remove the task associated with the stop."""
        self.properties['Task'] = ''
        self.properties['Reward'] = ''
        self.properties['Category'] = ''
        self.properties['Last Edit'] = int(datetime.datetime.now().strftime("%j"))

    def set_task(self, task):
        """Add a task to the stop."""
        if self.properties['Task'] == '':
            self.properties['Task'] = task.quest
            self.properties['Last Edit'] = int(datetime.datetime.now().strftime("%j"))
            self.properties['Category'] = task.reward_type
            self.properties['Reward'] = task.reward
            self.properties['Icon'] = task.icon
        else:
            raise TaskAlreadyAssigned(self, task)

    def add_nickname(self, nickname):
            """Add a nickname to a stop."""
            if 'Nicknames' not in self.properties:
                self.properties['Nicknames'] = []
            if (len(self.properties['Nicknames']) == 1 and self.properties['Nicknames'][0].startswith('temp')):
                self.properties['Nicknames'][0] = nickname.title()
            else:
                self.properties['Nicknames'].append(nickname.title())


class ResearchMap(pygeoj.GeojsonFile):  # TODO Add map boundary here and a default one that checks for proper long/lat formating
    """Class for the research map. Hopefully this will allow for multiple servers with seperate maps to be stored easily at once."""
    def __getitem__(self, index):
        """Get a feature based on its index, like geojfile[7]"""
        return Stop(self._data["features"][index])

    def __iter__(self):
        """Iterates through and yields each feature in the file."""
        for featuredict in self._data["features"]:
            yield Stop(featuredict)

    def add_stop(self, obj=None, geometry=None, properties=None):
        r"""
        Add a given feature. If obj isn't specified, geometry and properties can be set as         arguments directly.

        Parameters:
        - **obj**: Another feature instance, an object with the \_\_geo_interface__ or a        geojson dictionary of the Feature type.
        - **geometry** (optional): Anything that the Geometry instance can accept.
        - **properties** (optional): A dictionary of key-value property pairs.

        """
        properties = properties or {}
        if isinstance(obj, Stop):
            # instead of creating copy, the original feat should reference the same one that was added here
            feat = obj._data
        elif isinstance(obj, dict):
            feat = obj.copy()
        else:
            feat = Stop(geometry=geometry, properties=properties).__geo_interface__
        self._data["features"].append(feat)

    def find_stop(self, stop_name):
        """Find a stop within the map by its name or nickname."""
        stops_found = []
        for stop in self:
            if (stop.properties['Stop Name'].title() == stop_name.title() or stop_name.lower() in stop.properties['Nicknames']):
                if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
                    self.reset_all
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

    def new_stop(self, coordinates, name):   # TODO Add check for being in the map range
        """Add a new stop to the map."""
        self.add_stop(properties={'marker-size': 'medium', 'marker-symbol': '', 'marker-color': '#808080', 'Stop Name': name, 'Task': '', 'Reward': '',
                                  'Last Edit': int(datetime.datetime.now().strftime("%j")), 'Nicknames': []
                                  },
                      geometry={"type": "Point", "coordinates": coordinates, "bbox": [coordinates[0], coordinates[1], coordinates[0], coordinates[1]]})

    def reset_old(self):
        """Check for and reset only old stops in the map. This should get deprecated by moving the last edit to the map properties."""
        stops_reset = False
        for stop in self:
            if stop.properties['Last Edit'] != int(datetime.datetime.now().strftime("%j")):
                stop.reset()
                stops_reset = True
        return stops_reset

    def reset_all(self):
        """Reset all the stops in the map."""
        for stop in self:
            stop.reset()

    def remove_stop(self, stop):
        """Remove a stop from the map."""
        for i in range(len(self)):
            if self[i] is stop:
                del self[i]

    def set_reset_time(self, time):     # TODO Figure out how to implement this as a nonfeature property
        """Set the time (in UTC) that the map should be reset"""
        pass


# Custom functions
def load(filepath=None, data=None, **kwargs):
    """Modification of pygeoj.load to work with the ResearchMap class."""
    return ResearchMap(filepath, data, **kwargs)


def new():
    """Modification of pygeoj.new to work with the ResearchMap class."""
    return ResearchMap()


# Custom Exceptions
class PokemapException(Exception):
    """Base class for the module so all module exceptions can be caught together if needed."""

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


class TaskNotFound(PokemapException):
    """Exception for when task not found with the given search string."""

    def __init__(self):
        """Add message based on context of error."""
        self.message = "No task found with the given string."


class NicknameInUse(PokemapException):
    """Exception for when a nickname is already associated with a stop or task."""

    def __init__(self, task_or_stop):
        """Add message based on context of error."""
        if type(task_or_stop) is Task:
            task = task_or_stop
            self.message = "This nickname is already associated with the task: " + task.quest + ' for a ' + task.reward
        elif type(task_or_stop) is pygeoj.Feature:
            stop = task_or_stop
            self.message = "This nickname is already associated with the stop: " + stop.properties['Stop Name']
