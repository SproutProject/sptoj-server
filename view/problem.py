'''Problem view module'''


import config
import model.problem
import re
import os
import stat
import fcntl
import json
import binascii
import git
import asyncio
from model.user import UserLevel
from . import APIHandler, Attribute, Interface


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


class UpdateHandler(APIHandler):
    '''Update handler.'''

    level = UserLevel.kernel

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): {}

        Returns:
            'Success'

        '''

        await self.update()

        return 'Success'

    async def update(self):
        '''Scan the problem directory and update database.'''

        loop = asyncio.get_event_loop()
        task = loop.run_in_executor(None, UpdateHandler.sync_git,
            config.PROBLEM_DIR)
        revision, paths = await task
        
        uids = set()
        for path in paths:
            #TODO This is for linux only.
            parts = re.findall('^(\d+)', path)
            if len(parts) == 1:
                uids.add(int(parts[0]))

        for uid in uids:
            metadata = await self.load_problem(uid)
            if metadata is None:
                await model.problem.remove(uid)
            else:
                await model.problem.create(uid, revision, metadata)

    async def load_problem(self, uid):
        '''Try to load the problem.
        
        Args:
            uid (int): Problem ID.

        Returns:
            Object | None
        
        '''

        try:
            problem_path = os.path.join(config.PROBLEM_DIR, str(uid))
            assert stat.S_ISDIR(os.lstat(problem_path).st_mode)
            config_path = os.path.join(problem_path, 'conf.json')
            assert stat.S_ISREG(os.lstat(config_path).st_mode)

            with open(config_path, 'r') as config_file:
                return json.load(config_file)
        except:
            return None

    def sync_git(git_dir):
        '''Sync the git and return the different paths.
        
        Args:
            git_dir (string): The git directory.

        Returns:
            (string, [string])
        
        '''

        # Prevent from race condition.
        lockfd = os.open(os.path.join(git_dir, '.flock'),
            os.O_CREAT | os.O_CLOEXEC, 0o440)
        fcntl.flock(lockfd, fcntl.LOCK_EX)

        try:
            repo = git.Repo(git_dir)
            current = repo.heads.current
            upstream = repo.heads.master
            if current.commit == upstream.commit:
                return []

            diffs = upstream.commit.diff(current.commit)
            diff_paths = set()
            for diff in diffs:
                diff_paths.add(diff.a_path)
                diff_paths.add(diff.b_path)

            current.commit = upstream.commit
            current.checkout()
            repo.head.reset(index=True, working_tree=True)

            revision = binascii.hexlify(current.commit.binsha).decode('utf-8')
            return (revision, list(diff_paths))
        finally:
            fcntl.flock(lockfd, fcntl.LOCK_UN)
            os.close(lockfd)


class ListHandler(APIHandler):
    '''List handler.'''

    level = UserLevel.kernel

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): {}

        Returns:
            [ProblemInterface] | 'Error'

        '''

        problems = await model.problem.get_list()
        if problems is None:
            return 'Error'

        return [ProblemInterface(problem) for problem in problems]
