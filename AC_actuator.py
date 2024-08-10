from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from helper_functions import publish_state_change

class ACActuatorBehaviour(FSMBehaviour):
    def __init__(self):
        super().__init__()
        
    async def on_start(self):
        print("ACActuator: behaviour starting")  
        with open('agent_addresses.txt', 'a') as f:
            f.write(f";{self.agent.jid}\n")      
                  
    async def on_end(self):
        print("ACActuator: behaviour ending")

class StateOn(State):
    async def run(self):   
        print("ACActuator: The AC unit is on")      
        self.set('state','on')
        self.set_next_state('StateWaitingForCommand')
        
class StateOff(State):
    async def run(self):      
        print("ACActuator: The AC unit is off")         
        self.set('state','off')
        self.set_next_state('StateWaitingForCommand')

class StateWaitingForCommand(State):
    async def run(self):     
        command = 0 
        while command == 0:   
            await publish_state_change('acActuator', 'acState', 'actuators', self.get('state'), self)
            msg = await self.receive(timeout=10)
            print("ACActuator: I am waiting for a command message")   
            if msg:      
                if msg.metadata.get("type") == "acCommand" and msg.metadata.get("ontology") == "controllers":
                    print("ACActuator: I have received a command: " + msg.body) 
                    command = 1
                    command_msg = msg   
       
        if command_msg.body == "on":
            self.set_next_state('StateOn')
        else:
            self.set_next_state('StateOff')

class StateInitialize(State):
    async def run(self):
        msg = await self.receive(timeout=60)
        if msg.body == "initialize":
            await publish_state_change('acActuator', 'acState', 'actuators', "off", self) 
            self.set('state','off')
            print("ACActuator: initialized")
            self.set_next_state('StateWaitingForCommand') 
        else: 
            self.set_next_state('StateInitialize')

class ACActuatorAgent(Agent):
    async def setup(self):
        fsm = ACActuatorBehaviour()
        fsm.add_state(name="StateOn", state=StateOn())
        fsm.add_state(name="StateOff", state=StateOff())
        fsm.add_state(name="StateWaitingForCommand", state=StateWaitingForCommand())    
        fsm.add_state(name="StateInitialize", state=StateInitialize(), initial=True)   
        
        fsm.add_transition(source="StateWaitingForCommand", dest="StateOn")
        fsm.add_transition(source="StateWaitingForCommand", dest="StateOff")
        fsm.add_transition(source="StateOn", dest="StateWaitingForCommand")
        fsm.add_transition(source="StateOff", dest="StateWaitingForCommand")
        fsm.add_transition(source="StateInitialize", dest="StateWaitingForCommand")
        fsm.add_transition(source="StateInitialize", dest="StateInitialize")

        self.add_behaviour(fsm)