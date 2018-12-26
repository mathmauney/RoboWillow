"""This module implements the functions and classes for making maps of research tasks in pokemon go."""

import datetime
import pygeoj


class Task:
    """Research task class, specified by the display name and quest."""

    def __init__(self, name, quest, shiny=False):
        """Initialize the task object and parse the input name into the rewards if possible."""
        self.name = name
        self.quest = quest
        self.shiny = shiny
        self.nicknames = []
        if 'Rare' in name:    # Check to see what the reward type is
            self.reward_type = 'Rare Candy'
        elif 'Stardust' in name:
            self.reward_type = 'Stardust'
        else:
            self.reward_type = 'Encounter'
        if ' or ' in name:  # Try to parse the name into rewards
            self.reward = name.split(' or ')
        elif 'Gen 1' in name:
            self.reward = ['Bulbasaur', 'Squirtle', 'Charmander']
        else:
            self.reward = [name]


class Tasklist:
    """Future class if the tasklist ends up needing one."""

    pass


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
        else:
            raise TaskAlreadyAssigned(self, task)


class ResearchMap(pygeoj.GeojsonFile):
    """Class for the research map. Hopefully this will allow for multiple servers with seperate maps to be stored easily at once."""

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
        feat.map = self
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
