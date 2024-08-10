from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from helper_functions import publish_state_change

class BlindsActuatorBehaviour(FSMBehaviour):
    def __init__(self):
        super().__init__()

    async def on_start(self):
        print("BlindsActuator: behaviour starting")  
        with open('agent_addresses.txt', 'a') as f:
            f.write(f";{self.agent.jid}\n")      
                  
    async def on_end(self):
        print("BlindsActuator: behaviour ending")

class StateOpen(State):
    async def run(self):   
        print("BlindsActuator: the blinds are open")
        self.set('state','open')    
        self.set_next_state('StateWaitingForCommand')
        
class StateClosed(State):
    async def run(self):      
        print("BlindsActuator: the blinds are closed")    
        self.set('state','closed')       
        self.set_next_state('StateWaitingForCommand')

class StateWaitingForCommand(State):    
    async def run(self):      
        command = 0
        while command == 0:   
            await publish_state_change('blindsActuator', 'blindsState', 'actuators', self.get('state'), self)
            print("BlindsActuator: I am waiting for a command message")    
            msg = await self.receive(timeout=10)       
            if msg:                   
                if msg.metadata.get("type") == "blindsCommand" and msg.metadata.get("ontology") == "controllers":
                    print("BlindsActuator: I have received a command: " + msg.body) 
                    command = 1
                    command_msg = msg   

        if command_msg.body == "open":
            self.set_next_state('StateOpen')
        else:
            self.set_next_state('StateClosed')

class StateInitialize(State):
    async def run(self):
        msg = await self.receive(timeout=60)
        if msg.body == "initialize":
            await publish_state_change('blindsActuator', 'blindsState', 'actuators', 'closed', self)
            self.set('state', 'closed')      
            print("BlindsActuator: initialized")   
            self.set_next_state('StateWaitingForCommand') 
        else: 
            self.set_next_state('StateInitialize')

class BlindsActuatorAgent(Agent):
    async def setup(self):
        fsm = BlindsActuatorBehaviour()
        fsm.add_state(name="StateOpen", state=StateOpen())
        fsm.add_state(name="StateClosed", state=StateClosed())      
        fsm.add_state(name="StateWaitingForCommand", state=StateWaitingForCommand())     
        fsm.add_state(name="StateInitialize", state=StateInitialize(), initial=True)   
        
        fsm.add_transition(source="StateWaitingForCommand", dest="StateOpen")
        fsm.add_transition(source="StateWaitingForCommand", dest="StateClosed")
        fsm.add_transition(source="StateOpen", dest="StateWaitingForCommand")
        fsm.add_transition(source="StateClosed", dest="StateWaitingForCommand")
        fsm.add_transition(source="StateInitialize", dest="StateWaitingForCommand")    
        fsm.add_transition(source="StateInitialize", dest="StateInitialize")

        self.add_behaviour(fsm)