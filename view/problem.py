'''Problem view module'''


import config
import model.problem
import model.scoring
import view.proset
import re
import os
import stat
import fcntl
import json
import binascii
import git
import asyncio
from model.user import UserLevel
from .interface import *
from . import APIHandler


async def get_problem(user, uid):
    '''Check permission and get the problem.

    Args:
        user (UserModel): User.
        uid (int): Problem ID.

    Returns:
        ProblemModel | None

    '''

    problem = await model.problem.get(uid)
    if problem is None:
        return None

    if await view.proset.is_problem_hidden(user, problem.uid):
        return None

    return problem


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
            diff_paths = set()
            repo = git.Repo(git_dir)
            current = repo.heads.current
            upstream = repo.heads.master
            if current.commit != upstream.commit:
                diffs = upstream.commit.diff(current.commit)
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


class GetHandler(APIHandler):
    '''Get handler.'''

    async def process(self, uid, data):
        '''Process the request.

        Args:
            data (object: {})

        Returns:
            {
                'problem': ProblemInterface,
                'rate': [ProblemRateInterface] optional
            } | 'Error'

        '''

        uid = int(uid)
        problem = await get_problem(self.user, uid)
        if problem is None:
            return 'Error'

        ret = { 'problem': ProblemInterface(problem) }

        if self.user is not None:
            rate_list = await model.scoring.get_problem_rate(self.user.category,
                problem.uid)
            if rate_list is not None:
                ret['rate'] = [ProblemRateInterface(rate) for rate in rate_list]

        return ret


class StaticHandler(APIHandler):
    '''Serve problem static files.'''

    async def retrieve(self, uid, rel_path):
        '''Process the request.

        Args:
            uid (int): Problem ID.
            rel_path (string): Relative path. (Assert it has been normalized.)

        '''

        uid = int(uid)
        problem = await get_problem(self.user, uid)
        if problem is None:
            self.set_status(404)
            return

        self.set_header('x-accel-redirect',
            '/internal/static/{}/http/{}'.format(problem.uid, rel_path))

        self.set_status(200)


class SubmitHandler(APIHandler):
    '''Submit handler.'''

    level = UserLevel.user

    async def process(self, uid, data):
        '''Process the request.

        Args:
            uid (int): Problem ID.
            data (object): { 'code' (string), 'lang' (string) }

        Returns:
            Int | 'Error'

        '''

        uid = int(uid)
        code = data['code']
        lang = data['lang']

        if len(code) > config.CODE_LIMIT:
            return 'Error'

        problem = await get_problem(self.user, uid)
        if problem is None:
            return 'Error'

        challenge = await model.challenge.create(self.user, problem)
        if challenge is None:
            return 'Error'

        loop = asyncio.get_event_loop()
        task = loop.run_in_executor(None, SubmitHandler.store_code,
            challenge.uid, code)
        code_path = await task
        if code_path is None:
            await challenge.remove()
            return 'Error'

        # Wait the challange.
        await view.challenge.emit_challenge(challenge, code_path)

        return challenge.uid

    def store_code(challenge_uid, code):
        '''Store the submitted code.

        Args:
            challenge_uid (int): Challenge ID.
            code (string): Code.

        Returns:
            String | None

        '''

        code_root = os.path.join(config.CODE_DIR, '{}'.format(challenge_uid))
        code_main = os.path.join(code_root, 'main.cpp')
        try:
            os.mkdir(code_root, mode=0o755)
            with open(code_main, 'w') as main_file:
                main_file.write(code)
            return code_main
        except:
            return None
