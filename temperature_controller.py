from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from helper_functions import publish_state_change
import asyncio
from spade.message import Message

class TemperatureControllerBehaviour(FSMBehaviour):
    async def on_start(self):
        print("TemperatureController: behaviour starting")  
        with open('agent_addresses.txt', 'a') as f:
            f.write(f"blindsActuator,radiatorActuator,heaterActuator,acActuator,tempSensor,motionState,resourceState;{self.agent.jid}\n")      
                  
    async def on_end(self):
        print("TemperatureController: behaviour ending")

class StateHeat(State):
    async def run(self):
        await publish_state_change('tempController', 'heatingState', 'controllers', 'heating', self)
        radiator = 0

        while radiator == 0 : 
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "radiatorState" and msg.metadata.get("ontology") == "actuators":
                radiator = 1
                radiator_msg = msg

        msg_radiator = Message(to="radiatoractuator@desktop-ms7hl0s")  
        msg_radiator.set_metadata("ontology", "controllers")  
        msg_radiator.set_metadata("type", "radiatorCommand")      

        msg_heater = Message(to="heateractuator@desktop-ms7hl0s")  
        msg_heater.set_metadata("ontology", "controllers")  
        msg_heater.set_metadata("type", "heaterCommand")    

        msg_ac = Message(to="acactuator@desktop-ms7hl0s")  
        msg_ac.set_metadata("ontology", "controllers")  
        msg_ac.set_metadata("type", "acCommand")
        msg_ac.body = "off"
        await self.send(msg_ac)   

        if self.get("resource_state") == "lowGas":
            print("TemperatureController: Turning on the electric heater")
            msg_heater.body = "on"
            await self.send(msg_heater)
        elif radiator_msg.body == "on":
            print("TemperatureController:  Turning on the electric heater") 
            msg_heater.body = "on"
            await self.send(msg_heater)
        else:            
             print("TemperatureController:  Turning on the radiator") 
             msg_radiator.body = "on"
             await self.send(msg_radiator)

        motion = 0
        heat = 0

        while motion == 0 or heat == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "motion" and msg.metadata.get("ontology") == "controllers":
                motion = 1
                motion_msg = msg
            elif msg.metadata.get("type") == "heat" and msg.metadata.get("ontology") == "sensors":
                heat = 1
                heat_msg = msg      

        self.set("temperature", heat_msg.body)

        if motion_msg.body == 'empty':            
            self.set_next_state("StateIdle")
        elif int(heat_msg.body) > int(self.get("max_temp")) or int (heat_msg.body) < int(self.get("min_temp")):    
            self.set_next_state("StateResourceCheck")       
        else:          
            self.set_next_state("StateIdle") 
        
class StateCool(State):
    async def run(self):        
        await publish_state_change('tempController', 'heatingState', 'controllers', 'cooling', self)
        blinds = 0

        while blinds == 0: 
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "blindsState" and msg.metadata.get("ontology") == "actuators":
                blinds = 1
                blinds_msg = msg   

        msg_ac = Message(to="acactuator@desktop-ms7hl0s")  
        msg_ac.set_metadata("ontology", "controllers")  
        msg_ac.set_metadata("type", "acCommand")      

        msg_blinds = Message(to="blindsactuator@desktop-ms7hl0s")  
        msg_blinds.set_metadata("ontology", "controllers")  
        msg_blinds.set_metadata("type", "blindsCommand")      

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

        if self.get("resource_state") == "lowElectricity":
            print("TemperatureController: Closing the blinds")
            msg_blinds.body = "close"
            await self.send(msg_blinds)            
        elif blinds_msg.body == "open":
            print("TemperatureController: Closing the blinds")
            msg_blinds.body = "close"
            await self.send(msg_blinds)    
        else:
            print("TemperatureController: Turning on AC")
            msg_ac.body = "on"
            await self.send(msg_ac)
       
        motion = 0
        heat = 0

        while motion == 0 or heat == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "motion" and msg.metadata.get("ontology") == "controllers":
                motion = 1
                motion_msg = msg
            elif msg.metadata.get("type") == "heat" and msg.metadata.get("ontology") == "sensors":
               heat = 1
               heat_msg = msg    
        
        self.set("temperature", heat_msg.body)

        if motion_msg.body == 'empty':            
            self.set_next_state("StateIdle")
        elif int(heat_msg.body) > int(self.get("max_temp")) or int (heat_msg.body) < int(self.get("min_temp")): 
            self.set_next_state("StateResourceCheck")       
        else:          
            self.set_next_state("StateIdle") 

class StateResourceCheck(State):
    async def run(self):
        print("TemperatureController: Querying Resource Controller")
        resource = 0

        while resource == 0:
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "resource" and msg.metadata.get("ontology") == "controllers":
                resource = 1
                resource_msg = msg

        if resource_msg.body == "critical":
            self.set_next_state("StateCritical")
        else:            
            self.set("resource_state",  resource_msg.body) 
            temperature = self.get("temperature")
            if int(temperature) > int(self.get("max_temp")):
                self.set_next_state("StateCool")
            elif int(temperature) < int(self.get("min_temp")):
                self.set_next_state("StateHeat")
            else:
                self.set_next_state("StateIdle")

class StateIdle(State):
    async def run(self):
        print("TemperatureController: The temperature is as desired or the room is empty")
        motion = 0
        heat = 0      
        await publish_state_change('tempController', 'heatingState', 'controllers', 'idle', self)

        while motion == 0 or heat == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "motion" and msg.metadata.get("ontology") == "controllers":
                motion = 1
                motion_msg = msg
            elif msg.metadata.get("type") == "heat" and msg.metadata.get("ontology") == "sensors":
                heat = 1
                heat_msg = msg            
        
        self.set("temperature", heat_msg.body)
        
        if motion_msg.body == 'empty':           
            self.set_next_state("StateIdle")
        elif int(heat_msg.body) > int(self.get("max_temp")) or int (heat_msg.body) < int(self.get("min_temp")):      
            self.set_next_state("StateResourceCheck")       
        else:          
            self.set_next_state("StateIdle") 

class StateCritical(State):
    async def run(self):
        print("TemperatureController: There are no resources for heating")
        print("TemperatureController: Please check your solar panels and your gas reserves")      
        self.set_next_state("StateIdle") 

class StateSetTemperature(State):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state

    async def run(self):
        min_temp = int(self.shared_state.get_desired_temp()) - 2
        max_temp = int(self.shared_state.get_desired_temp()) + 2
        self.set("min_temp", min_temp)
        self.set("max_temp", max_temp)
        print(f"TemperatureController: max temperature set to {max_temp}, min temp set to {min_temp}")

        await asyncio.sleep(5)      

        print("TemperatureController: Initializing actuators")
        msg_radiator = Message(to="radiatoractuator@desktop-ms7hl0s")  
        msg_radiator.set_metadata("ontology", "controllers")  
        msg_radiator.set_metadata("type", "radiatorCommand")  
        msg_radiator.body = "initialize"    

        msg_heater = Message(to="heateractuator@desktop-ms7hl0s")  
        msg_heater.set_metadata("ontology", "controllers")  
        msg_heater.set_metadata("type", "heaterCommand")    
        msg_heater.body = "initialize"

        msg_ac = Message(to="acactuator@desktop-ms7hl0s")  
        msg_ac.set_metadata("ontology", "controllers")  
        msg_ac.set_metadata("type", "acCommand")    
        msg_ac.body = "initialize"

        await self.send(msg_radiator)
        await self.send(msg_heater)
        await self.send(msg_ac)

        self.set_next_state("StateIdle")

class TemperatureControllerAgent(Agent):
    async def setup(self):
        fsm = TemperatureControllerBehaviour()
        fsm.add_state(name="StateHeat", state=StateHeat())
        fsm.add_state(name="StateCool", state=StateCool())
        fsm.add_state(name="StateResourceCheck", state=StateResourceCheck())
        fsm.add_state(name="StateIdle", state=StateIdle())      
        fsm.add_state(name="StateSetTemperature", state=StateSetTemperature(shared_state = self.state), initial=True)  
        fsm.add_state(name="StateCritical", state=StateCritical())
        
        fsm.add_transition(source="StateSetTemperature", dest="StateIdle")
        fsm.add_transition(source="StateHeat", dest="StateResourceCheck")
        fsm.add_transition(source="StateHeat", dest="StateIdle")
        fsm.add_transition(source="StateCool", dest="StateIdle")
        fsm.add_transition(source="StateCool", dest="StateResourceCheck")
        fsm.add_transition(source="StateIdle", dest="StateResourceCheck")
        fsm.add_transition(source="StateIdle", dest="StateIdle")
        fsm.add_transition(source="StateResourceCheck", dest="StateCool")
        fsm.add_transition(source="StateResourceCheck", dest="StateHeat")
        fsm.add_transition(source="StateResourceCheck", dest="StateIdle")
        fsm.add_transition(source="StateResourceCheck", dest="StateCritical")
        fsm.add_transition(source="StateCritical", dest="StateIdle")
        
        self.add_behaviour(fsm)