'''View interface module'''


from . import Attribute, Interface


class PartialListInterface(Interface):
    '''General list view interface.'''

    count = Attribute(optional=True)
    data = Attribute()

    def __init__(self, data, count=None):
        '''Initialize.

        Args:
            data ([Interface | None]): List data.
            count (int): Total count.

        '''

        self.data = data
        if count is not None:
            self.count = count


class UserInterface(Interface):
    '''User view interface.'''

    uid = Attribute()
    mail = Attribute()
    name = Attribute()
    level = Attribute()
    category = Attribute()

    def __init__(self, user):
        '''Initialize.

        Args:
            user (UserModel): User model.

        '''

        self.uid = user.uid
        self.mail = user.mail
        self.name = user.name
        self.level = int(user.level)
        self.category = int(user.category)


class ProfileInterface(Interface):
    '''Profile view interface.'''

    uid = Attribute()
    name = Attribute()
    category = Attribute()
    rate = Attribute(optional=True)

    def __init__(self, user, rate=None):
        '''Initialize.

        Args:
            user (UserModel): User model.
            rate (int | None): User rate.

        '''

        self.uid = user.uid
        self.name = user.name
        self.category = int(user.category)
        if rate is not None:
            self.rate = rate


class UserStatisticInterface(Interface):
    '''User statistic view interface.'''

    tried_problems = Attribute()

    def __init__(self, tried_problems):
        '''Initialize.

        Args:
            tried_problems ({
                problem_uid: { result: int },
                ...
            }): Tried problems

        '''

        self.tried_problems = tried_problems


class ProblemInterface(Interface):
    '''Problem view interface.'''

    uid = Attribute()
    revision = Attribute()
    name = Attribute()
    timelimit = Attribute()
    memlimit = Attribute()
    lang = Attribute()
    checker = Attribute()
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
        self.subtask = [ test['weight'] for test in problem.metadata['test'] ]


class ProblemRateInterface(Interface):
    '''Problem subtask view interface.'''

    index = Attribute()
    count = Attribute()
    score = Attribute()

    def __init__(self, problem_rate):
        '''Initialize.

        Args:
            problem_rate ({
                index (int),
                count (int),
                score (int)
            }): Problem rate.

        '''

        self.index = problem_rate['index']
        self.count = problem_rate['count']
        self.score = problem_rate['score']


class ProSetInterface(Interface):
    '''Problem set view interface.'''

    uid = Attribute()
    name = Attribute()
    hidden = Attribute()
    metadata = Attribute()

    def __init__(self, proset):
        '''Initialize.

        Args:
            proset (ProSetModel): Problem set model.

        '''

        self.uid = proset.uid
        self.name = proset.name
        self.hidden = proset.hidden
        self.metadata = proset.metadata


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
    subtasks = Attribute(optional=True)
    code = Attribute(optional=True)

    def __init__(self, challenge, subtasks=None, code=None,
        hidden_verdict=True):
        '''Initialize.

        Args:
            challenge (ChallengeModel): Challenge model.

        '''

        self.uid = challenge.uid
        self.state = int(challenge.state)
        self.timestamp = challenge.timestamp
        self.submitter = ProfileInterface(challenge.submitter)
        self.problem = ProblemInterface(challenge.problem)

        self.metadata = {}
        if 'result' in challenge.metadata:
            self.metadata['result'] = challenge.metadata['result']
            self.metadata['runtime'] = challenge.metadata['runtime']
            self.metadata['memory'] = challenge.metadata['memory']

        if not hidden_verdict and 'verdict' in challenge.metadata:
            self.metadata['verdict'] = challenge.metadata['verdict']

        if subtasks is not None:
            self.subtasks = [SubtaskInterface(subtask) for subtask in subtasks]

        if code is not None:
            self.code = code


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
        self.metadata = {}
        if 'result' in subtask.metadata:
            self.metadata['result'] = subtask.metadata['result']
            self.metadata['runtime'] = subtask.metadata['runtime']
            self.metadata['memory'] = subtask.metadata['memory']


class RankerInterface(Interface):
    '''Ranker interface.'''

    profile = Attribute()
    rate = Attribute()
    results = Attribute()

    def __init__(self, profile, rate, results):
        '''Initialize.

        Args:
            user (ProfileModel): User profile.
            rate (int): Rate.
            results (object): Results.

        '''

        self.profile = profile
        self.rate = rate
        self.results = results


class RankInterface(Interface):
    '''Rank view interface.'''

    problems = Attribute()
    rankers = Attribute()

    def __init__(self, problems, rankers):
        '''Initialize.

        Args:
            problems ([int]): Problem IDs.
            rankders ([RankerInterface]): Rankders.

        '''

        self.problems = problems
        self.rankers = rankers
