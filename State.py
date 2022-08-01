class State:
    CurrentContext = None
    def __init__(self, Context):
        self.CurrentContext = Context
    def trigger(self):
        return True

class StateContext:
    state = None
    CurrentState = None
    availableStates = {}

    def setState(self, newstate):
        try:
            self.CurrentState = self.availableStates[newstate]
            self.state = newstate
            self.CurrentState.trigger()
            return True
        except KeyError: #incorrect state key specified
            return False

    def getStateIndex(self):
        return self.state

if __name__ == '__main__':
    MyContext = StateContext()
    for count in list(range(0,4)):
        MyContext.availableStates[count] = State(MyContext)
    print(MyContext.availableStates[1].CurrentContext)
    MyContext.setState(1)
    print(MyContext.getStateIndex())