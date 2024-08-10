from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import asyncio

class LightControllerBehaviour(FSMBehaviour):
    def __init__(self, state):
        super().__init__()
        self.state=state
        
    async def on_start(self):
        print("LightController: behaviour starting")     
        with open('agent_addresses.txt', 'a') as f:
            f.write(f"lightsActuator,blindsActuator,tempController,motionState,outLightSensor,inLightSensor;{self.agent.jid}\n")      
                  
    async def on_end(self):
        print("LightController: behaviour ending")

class StateIdle(State):
    async def run(self):      
        print("LightController: The light levels are as desired / the room is empty")
        indoorLight = 0
        motion = 0

        while indoorLight == 0 or motion == 0:
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "indoor_light" and msg.metadata.get("ontology") == "sensors":
                indoorLight = 1
                indoorLight_msg = msg     
            
            elif msg.metadata.get("type") == "motion" and msg.metadata.get("ontology") == "controllers":
                motion = 1
                motion_msg = msg
   
        if motion_msg.body == "empty":
            self.set_next_state('StateIdle')
        else: 
            if int(indoorLight_msg.body) > int(self.get("max_light")):
                self.set_next_state('StateHighLight')
            elif int(indoorLight_msg.body) < int(self.get("min_light")):
                self.set_next_state('StateLowLight')
            else:
                self.set_next_state('StateIdle')
        
class StateLowLight(State):
    async def run(self):              
        indoorLight = 0
        outdoorLight = 0
        heatingState = 0
        blinds = 0
        lights = 0
        motion = 0

        while outdoorLight == 0 or heatingState == 0 or blinds == 0 or lights == 0: 
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "outdoor_light" and msg.metadata.get("ontology") == "sensors":
                outdoorLight = 1
                outdoorLight_msg = msg   
            elif msg.metadata.get("type") == "heatingState" and msg.metadata.get("ontology") == "controllers":
                heatingState = 1
                heatingState_msg = msg   
            elif msg.metadata.get("type") == "lightsState" and msg.metadata.get("ontology") == "actuators":
                lights = 1
                lights_msg = msg
            elif msg.metadata.get("type") == "blindsState" and msg.metadata.get("ontology") == "actuators":
                blinds = 1
                blinds_msg = msg   

        msg_lights = Message(to="lightsactuator@desktop-ms7hl0s")  
        msg_lights.set_metadata("ontology", "controllers")  
        msg_lights.set_metadata("type", "lightsCommand")      

        msg_blinds = Message(to="blindsactuator@desktop-ms7hl0s")  
        msg_blinds.set_metadata("ontology", "controllers")  
        msg_blinds.set_metadata("type", "blindsCommand")    
     
        # bright day outside is 6000+ lumens, so let's say that blinds help at above 2000    
        if heatingState_msg.body != "cooling" and int(outdoorLight_msg.body) > 2000 and blinds_msg.body != "open":
            print("LightController: Opening blinds")
            msg_blinds.body = "open"
            await self.send(msg_blinds)            
        elif lights_msg.body == "on":
            print("LightController: Opening blinds")
            msg_blinds.body = "open"
            await self.send(msg_blinds)
        else:
            print("LightController: Turning on the lights")  
            msg_lights.body = "on"
            await self.send(msg_lights)     

        while indoorLight == 0 or motion == 0:
                msg = await self.receive(timeout=30)
                if msg.metadata.get("type") == "indoor_light" and msg.metadata.get("ontology") == "sensors":
                    indoorLight = 1
                    indoorLight_msg = msg     
                elif msg.metadata.get("type") == "motion" and msg.metadata.get("ontology") == "controllers":
                    motion = 1
                    motion_msg = msg

        if motion_msg.body == "empty":
            self.set_next_state('StateIdle')
        else: 
            if int(indoorLight_msg.body) > int(self.get("max_light")):
                self.set_next_state('StateHighLight')
            elif int(indoorLight_msg.body) < int(self.get("min_light")):
                self.set_next_state('StateLowLight')
            else:
                self.set_next_state('StateIdle')


class StateHighLight(State):
    async def run(self):              
        indoorLight = 0
        outdoorLight = 0
        heatingState = 0
        blinds = 0
        lights = 0
        motion = 0

        while outdoorLight == 0 or heatingState == 0 or blinds == 0 or lights == 0: 
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "outdoor_light" and msg.metadata.get("ontology") == "sensors":
                outdoorLight = 1
                outdoorLight_msg = msg   
            elif msg.metadata.get("type") == "heatingState" and msg.metadata.get("ontology") == "controllers":
                heatingState = 1
                heatingState_msg = msg   
            elif msg.metadata.get("type") == "lightsState" and msg.metadata.get("ontology") == "actuators":
                lights = 1
                lights_msg = msg
            elif msg.metadata.get("type") == "blindsState" and msg.metadata.get("ontology") == "actuators":
                blinds = 1
                blinds_msg = msg     

        msg_lights = Message(to="lightsactuator@desktop-ms7hl0s")  
        msg_lights.set_metadata("ontology", "controllers")  
        msg_lights.set_metadata("type", "lightsCommand")      

        msg_blinds = Message(to="blindsactuator@desktop-ms7hl0s")  
        msg_blinds.set_metadata("ontology", "controllers")  
        msg_blinds.set_metadata("type", "blindsCommand")    
                              
        if blinds_msg.body == 'closed':
            print("LightController: Turning off the lights")
            msg_lights.body = "off"
            await self.send(msg_lights)
        elif int(outdoorLight_msg.body) > 2000 or lights_msg.body == 'off':
            print("LightController: Closing the blinds")
            msg_blinds.body = "close"
            await self.send(msg_blinds)
        else:    
            print("LightController: Turning off the lights")    
            msg_lights.body = "off"
            await self.send(msg_lights)   

        while indoorLight == 0 or motion == 0:
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "indoor_light" and msg.metadata.get("ontology") == "sensors":
                indoorLight = 1
                indoorLight_msg = msg     
            elif msg.metadata.get("type") == "motion" and msg.metadata.get("ontology") == "controllers":
                motion = 1
                motion_msg = msg

        if motion_msg.body == "empty":
            self.set_next_state('StateIdle')
        else: 
            if int(indoorLight_msg.body) > int(self.get("max_light")):
                self.set_next_state('StateHighLight')
            elif int(indoorLight_msg.body) < int(self.get("min_light")):
                self.set_next_state('StateLowLight')
            else:
                self.set_next_state('StateIdle')

class StateSetLightLevel(State):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state

    async def run(self):
        min_light = int(self.shared_state.get_desired_light()) - 40
        max_light = int(self.shared_state.get_desired_light()) + 40
        self.set("min_light", min_light)
        self.set("max_light", max_light)
        print("LightController: max light level (lumens per m2) set to " + str(max_light) + ", min light level set to " + str(min_light))

        await asyncio.sleep(5)      

        print("LightController: Initializing actuators")
        msg_lights = Message(to="lightsactuator@desktop-ms7hl0s")  
        msg_lights.set_metadata("ontology", "controllers")  
        msg_lights.set_metadata("type", "lightsCommand")  
        msg_lights.body = "initialize"    

        msg_blinds = Message(to="blindsactuator@desktop-ms7hl0s")  
        msg_blinds.set_metadata("ontology", "controllers")  
        msg_blinds.set_metadata("type", "blindsCommand")    
        msg_blinds.body = "initialize"

        await self.send(msg_lights)
        await self.send(msg_blinds)
        self.set_next_state("StateIdle")

class LightControllerAgent(Agent):
    async def setup(self):
        state = self.state
        fsm = LightControllerBehaviour(state = state)
        fsm.add_state(name="StateIdle", state=StateIdle())
        fsm.add_state(name="StateHighLight", state=StateHighLight())
        fsm.add_state(name="StateLowLight", state=StateLowLight())
        fsm.add_state(name="StateSetLightLevel", state=StateSetLightLevel(shared_state = self.state), initial=True) 
        
        fsm.add_transition(source="StateSetLightLevel", dest="StateIdle")
        fsm.add_transition(source="StateIdle", dest="StateIdle")
        fsm.add_transition(source="StateIdle", dest="StateLowLight")
        fsm.add_transition(source="StateIdle", dest="StateHighLight")
        fsm.add_transition(source="StateLowLight", dest="StateIdle")
        fsm.add_transition(source="StateLowLight", dest="StateLowLight")
        fsm.add_transition(source="StateLowLight", dest="StateHighLight")
        fsm.add_transition(source="StateHighLight", dest="StateIdle")
        fsm.add_transition(source="StateHighLight", dest="StateLowLight")
        fsm.add_transition(source="StateHighLight", dest="StateHighLight")      
        
        self.add_behaviour(fsm)