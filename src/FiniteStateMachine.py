class FiniteStateMachine:

    states = [
        "start",
        "launch",
        "loggedin",
        "whois",
        "whois_unknown",
        "whois_known",
        "whois_known_fresh",
        "whois_known_continue",
        "newuser",
        "noprofile",
        "continue",
        "not_continue",
        "recommendation",
        "answer"
    ]

    transitions = [
        ("start", "launch"),
        ("launch", "loggedin"),
        ("launch", "whois"),
        ("launch", "whois_unknown"),
        ("whois", "whois_known"),
        ("whois", "whois_unknown"),
        ("whois_unknown", "noprofile"),
        ("whois_unknown", "newuser"),
        ("whois_known", "whois_known_fresh"),
        ("whois_known", "whois_known_continue"),
        ("whois_known_continue", "continue"),
        ("whois_known_continue", "not_continue"),
        ("whois_known_fresh", "recommendation"),
        ("continue", "answer"),
        ("continue", "recommendation"),
        ("not_continue", "recommendation"),
        ("answer", "recommendation"),
        ("recommendation", "answer"),
        ("answer", "answer")
    ]

    start = "start"
    end = "end"
    currentState = ""

    def __init__(self):
        self.currentState = self.start

    # sets the start node
    def initFSM(self):
        self.currentState = self.start
        return self.currentState

    # returns current fsm state
    def getState(self):
        return self.currentState

    # sets new state if new state and transition is valid
    def setState(self, state):
        if self.checkState(state) and self.checkTransition(state):
            self.currentState = state
            print self.currentState
        return self.currentState

    # checks if state exists
    def checkState(self, state):
        return (state in self.states)

    # checks if transition is valid
    def checkTransition(self, state):
        return ((self.currentState, state) in self.transitions)

    # sets state of loaded session
    def loadStateFromSession(self, state):
        self.currentState = state
        return

    # checks if a state is the current state
    def isCurrentState(self, state):
        return (state == self.currentState)
