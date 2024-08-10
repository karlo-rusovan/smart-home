from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from helper_functions import publish_state_change

class ResourceControllerBehaviour(FSMBehaviour):
    async def on_start(self):
        print("ResourceController: behaviour starting")
        with open('agent_addresses.txt', 'a') as f:
            f.write(f"electricitySensor,gasSensor;{self.agent.jid}\n")
                  
    async def on_end(self):
        print("ResourceController: behaviour ending")

class StateOptimum(State):
    async def run(self):        
        print("ResourceController: Resources are at a good level")
        await publish_state_change('resourceState', 'resource', 'controllers', 'good', self)

        gas = 0
        electricity = 0

        while gas == 0 or electricity == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "gas" and msg.metadata.get("ontology") == "sensors":                
                gas = msg.body
            elif msg.metadata.get("type") == "electricity" and msg.metadata.get("ontology") == "sensors":
                electricity = msg.body
     
        if gas == 'low' and electricity == 'low':         
            self.set_next_state("StateCritical")
        elif gas == 'low':
            self.set_next_state("StateLowGas")
        elif electricity == 'low':
            self.set_next_state("StateLowElectricity")
        else:
            self.set_next_state("StateOptimum")
        
class StateLowGas(State):
    async def run(self):
        print("ResourceController: Gas is low/empty")
        await publish_state_change('resourceState', 'resource', 'controllers', 'lowGas', self)  

        gas = 0
        electricity = 0

        while gas == 0 or electricity == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "gas" and msg.metadata.get("ontology") == "sensors":                
                gas = msg.body
            elif msg.metadata.get("type") == "electricity" and msg.metadata.get("ontology") == "sensors":
                electricity = msg.body
        
        if gas == 'low' and electricity == 'low':         
            self.set_next_state("StateCritical")
        elif gas == 'low':
            self.set_next_state("StateLowGas")
        elif electricity == 'low':
            self.set_next_state("StateLowElectricity")
        else:
            self.set_next_state("StateOptimum")

class StateLowElectricity(State):
    async def run(self):
        print("ResourceController: Electricity is low/empty")
        await publish_state_change('resourceState', 'resource', 'controllers', 'lowElectricity', self)    
   
        gas = 0
        electricity = 0

        while gas == 0 or electricity == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "gas" and msg.metadata.get("ontology") == "sensors":                
                gas = msg.body
            elif msg.metadata.get("type") == "electricity" and msg.metadata.get("ontology") == "sensors":
                electricity = msg.body
     
        if gas == 'low' and electricity == 'low':         
            self.set_next_state("StateCritical")
        elif gas == 'low':
            self.set_next_state("StateLowGas")
        elif electricity == 'low':
            self.set_next_state("StateLowElectricity")
        else:
            self.set_next_state("StateOptimum")

class StateCritical(State):
    async def run(self):
        print("ResourceController: critical state, no resources")
        await publish_state_change('resourceState', 'resource', 'controllers', 'critical', self)   
   
        gas = 0
        electricity = 0

        while gas == 0 or electricity == 0:            
            msg = await self.receive(timeout=30)
            if msg.metadata.get("type") == "gas" and msg.metadata.get("ontology") == "sensors":                
                gas = 1
                gas_msg = msg
            elif msg.metadata.get("type") == "electricity" and msg.metadata.get("ontology") == "sensors":
                electricity = 1
                electricity_msg = msg

        if gas_msg.body == 'low' and electricity_msg.body == 'low':         
            self.set_next_state("StateCritical")
        elif gas_msg.body == 'low':
            self.set_next_state("StateLowGas")
        elif electricity_msg.body == 'low':
            self.set_next_state("StateLowElectricity")
        else:
            self.set_next_state("StateOptimum")

class ResourceControllerAgent(Agent):
    async def setup(self):  

        fsm = ResourceControllerBehaviour()
        fsm.add_state(name="StateOptimum", state=StateOptimum(), initial=True)
        fsm.add_state(name="StateLowGas", state=StateLowGas())     
        fsm.add_state(name="StateLowElectricity", state=StateLowElectricity()) 
        fsm.add_state(name="StateCritical", state=StateCritical())    
        
        fsm.add_transition(source="StateOptimum", dest="StateLowGas")
        fsm.add_transition(source="StateOptimum", dest="StateLowElectricity")
        fsm.add_transition(source="StateLowGas", dest="StateOptimum")
        fsm.add_transition(source="StateLowGas", dest="StateCritical")
        fsm.add_transition(source="StateLowElectricity", dest="StateCritical")
        fsm.add_transition(source="StateOptimum", dest="StateCritical")
        fsm.add_transition(source="StateCritical", dest="StateLowElectricity")
        fsm.add_transition(source="StateCritical", dest="StateLowGas")
        fsm.add_transition(source="StateCritical", dest="StateCritical")
        fsm.add_transition(source="StateCritical", dest="StateOptimum")
        fsm.add_transition(source="StateLowGas", dest="StateLowGas")
        fsm.add_transition(source="StateLowElectricity", dest="StateLowElectricity")
        fsm.add_transition(source="StateOptimum", dest="StateOptimum")
        
        self.add_behaviour(fsm)