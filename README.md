# RoboWillow

RoboWillow is a discord bot designed principly to facilitate the reporting and mapping of Pokemon Go research tasks. This is currently very much a work in process and shouldn't be deployed for anything other than testing. The rest of this README is still a template at this point, and will be updated as the project gets more finalized. 

## Getting Started

Don't get started with this yet, wait for the bot to get a bit more functional.

### Prerequisites


### Installing


## Current Features

### Research Map

A leaflet map based on the bot's geoJSON data can be found [here](https://mathmauney.github.io/RoboWillow/). Tasks for a stop can be viewed by clicking on a stop if a task has been reported. The map also supports filtering the tasks by reward and has custom icons for some tasks.

### Discord Bot

The discord bot supports rudimentary task reporting and mapping. Tasks are currently reset on first bot interaction after midnight. Current commands include:

```
addstop "Stop Name" latitude longitude
```

Adds a new stop to the map at the defined latitude and longitude

```
addtask "Reward" "Quest Requirements" "Reward Type" canBeShiny
```

Adds a new task to the bot's internal tasklist. The canBeShiny parameter should be either True or False

```
listtasks
```

Lists all tasks the bot currently knows along with their rewards.

```
set task "Reward" "Stop Name"
```

Assigns a task to a stop

### To Do

## Map

* Finish Fleshing out custom icons for pokemon tasks 
* Pull from bot geoJSON instead of statically defined test set

## Bot

* Handle task reset at midnight better. 
* Activate backups better once testing is finished
* Fill out help dialog better
* Better error handling when commands fail
* Move test bot onto a better hosting service than my personal computer


### About Project

## Authors

* **Alex Mauney** - *Initial work* - [MathMauney](https://github.com/mathmauney)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

Not sure yet.
