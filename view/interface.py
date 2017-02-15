'''View interface module'''


from . import Attribute, Interface


class UserInterface(Interface):
    '''User view interface.'''

    uid = Attribute()
    name = Attribute()
    level = Attribute()

    def __init__(self, user):
        '''Initialize.

        Args:
            user (UserModel): User model.

        '''

        self.uid = user.uid
        self.name = user.name
        self.level = int(user.level)


class ProblemInterface(Interface):
    '''Problem view interface.'''

    uid = Attribute()
    revision = Attribute()
    name = Attribute()
    timelimit = Attribute()
    memlimit = Attribute()
    lang = Attribute()
    checker = Attribute()
    scoring = Attribute()
    subtask = Attribute()

    def __init__(self, problem):
        '''Initialize.

        Args:
            problem (ProblemModel): Problem model.

        '''

        self.uid = problem.uid
        self.revision = problem.revision
        self.name = problem.name
        self.timelimit = problem.metadata['timelimit']
        self.memlimit = problem.metadata['memlimit']
        self.lang = problem.metadata['compile']
        self.checker = problem.metadata['check']
        self.scoring = problem.metadata['score']
        self.subtask = [ test['weight'] for test in problem.metadata['test'] ]


class ProSetInterface(Interface):
    '''Problem set view interface.'''

    uid = Attribute()
    name = Attribute()
    hidden = Attribute()

    def __init__(self, proset):
        '''Initialize.

        Args:
            proset (ProSetModel): Problem set model.

        '''

        self.uid = proset.uid
        self.name = proset.name
        self.hidden = proset.hidden


class ProItemInterface(Interface):
    '''Problem item view interface.'''

    uid = Attribute()
    hidden = Attribute()
    deadline = Attribute()
    metadata = Attribute()
    problem = Attribute()

    def __init__(self, proitem):
        '''Initialize.

        Args:
            proitem (ProItemModel): Problem item model.

        '''

        self.uid = proitem.uid
        self.hidden = proitem.hidden
        self.deadline = proitem.deadline
        self.metadata = proitem.metadata
        self.problem = ProblemInterface(proitem.problem)


class ChallengeInterface(Interface):
    '''Challenge view interface.'''

    uid = Attribute()
    state = Attribute()
    timestamp = Attribute()
    metadata = Attribute()
    submitter = Attribute()
    problem = Attribute()
    subtasks = Attribute()

    def __init__(self, challenge, subtasks):
        '''Initialize.

        Args:
            challenge (ChallengeModel): Challenge model.

        '''

        self.uid = challenge.uid
        self.state = int(challenge.state)
        self.timestamp = challenge.timestamp
        self.metadata = challenge.metadata
        self.submitter = UserInterface(challenge.submitter)
        self.problem = ProblemInterface(challenge.problem)
        self.subtasks = [SubtaskInterface(subtask) for subtask in subtasks]


class SubtaskInterface(Interface):
    '''Subtask view interface.'''

    uid = Attribute()
    index = Attribute()
    state = Attribute()
    metadata = Attribute()

    def __init__(self, subtask):
        '''Initialize.

        Args:
            subtask (SubtaskModel): Subtask model.

        '''

        self.uid = subtask.uid
        self.index = subtask.index
        self.state = int(subtask.state)
        self.metadata = subtask.metadata
