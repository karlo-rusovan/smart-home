# smart-home
A Multi-agent smart home system which uses data from temperature, light and motion sensors to make decisions about the heating and lighting systems.
The Agents are implemented using SPADE, and are divided into three groups: Sensors, Controllers, Actuators.
Sensors are tasked with sending the data about current motion, temperature and light level states to the Controllers.
Controllers use that data to make decisions on what needs to be done regarding the Heating and Lighting systems to create a more comfortable state for the occupants.
Actuators are the ones that get commands from the controllers and are used as endpoints to turn the heating and lighting devices on and off.

The smart home system is based on an assumption of a one-room house which uses an outside gas tank and solar panels for power. The data for the sensors
is simulated by manually filling out UI fields, and the devices of course don't exist, so the actuators just write out which device they're turning on or off.
This serves a purpose of a demo on how communication between agents in a modular smart home system might look, and the focus is more on the ways in which agents share data.


