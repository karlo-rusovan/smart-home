from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.template import Template
from helper_functions import publish_state_change
from spade.message import Message

class MotionControllerBehaviour(FSMBehaviour):
    async def on_start(self):
        print("MotionController: behaviour starting")
        with open('agent_addresses.txt', 'a') as f:
            f.write(f"motionSensor;{self.agent.jid}\n")
                  
    async def on_end(self):
        print("MotionController: behaviour ending")

class StateOccupied(State):
    async def run(self):
        print("MotionController: The room is occupied")
        await publish_state_change('motionState', 'motion', 'controllers', 'occupied', self)
            
        motion = 0
        while motion == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "motion" and msg.metadata.get("ontology") == "sensors":                
                motion = msg.body

        if msg.body == "empty":
                self.set_next_state("StateEmpty")
        else:
                self.set_next_state("StateOccupied")       
        
class StateEmpty(State):
    async def run(self):
        print("MotionController: The room is empty, turning off the lights and the heating/cooling devices")        
        await publish_state_change('motionState', 'motion', 'controllers', 'empty', self)
      
        msg_radiator = Message(to="radiatoractuator@desktop-ms7hl0s")  
        msg_radiator.set_metadata("ontology", "controllers")  
        msg_radiator.set_metadata("type", "radiatorCommand")     
        msg_radiator.body = "off"
        await self.send(msg_radiator) 

        msg_heater = Message(to="heateractuator@desktop-ms7hl0s")  
        msg_heater.set_metadata("ontology", "controllers")  
        msg_heater.set_metadata("type", "heaterCommand")   
        msg_heater.body = "off"
        await self.send(msg_heater)  

        msg_ac = Message(to="acactuator@desktop-ms7hl0s")  
        msg_ac.set_metadata("ontology", "controllers")  
        msg_ac.set_metadata("type", "acCommand")   
        msg_ac.body = "off"
        await self.send(msg_ac) 

        msg_lights = Message(to="lightsactuator@desktop-ms7hl0s")  
        msg_lights.set_metadata("ontology", "controllers")  
        msg_lights.set_metadata("type", "lightsCommand")   
        msg_lights.body = "off"
        await self.send(msg_lights) 

        motion = 0               
        while motion == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "motion" and msg.metadata.get("ontology") == "sensors":                
                motion = msg.body
                               
        if msg.body == "empty":
                self.set_next_state("StateEmpty")
        else:
                self.set_next_state("StateOccupied")       

class MotionControllerAgent(Agent):
    async def setup(self):              
        fsm = MotionControllerBehaviour()
        fsm.add_state(name="StateOccupied", state=StateOccupied())
        fsm.add_state(name="StateEmpty", state=StateEmpty(), initial=True)        
        
        fsm.add_transition(source="StateOccupied", dest="StateEmpty")
        fsm.add_transition(source="StateEmpty", dest="StateOccupied")
        fsm.add_transition(source="StateOccupied", dest="StateOccupied")
        fsm.add_transition(source="StateEmpty", dest="StateEmpty")
        
        self.add_behaviour(fsm)