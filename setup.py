#!/usr/bin/env python

import importlib
import os
import subprocess
import sys
from glob import glob
from contextlib import contextmanager

from setuptools import Command, setup

project_dir = os.path.dirname(os.path.realpath(__file__))

try:
    tag = subprocess.check_output(
        [
            'git',
            '--no-pager',
            'describe',
            '--abbrev=0',
            '--tags',
        ],
        stderr=subprocess.DEVNULL,
    ).strip().decode()
except subprocess.CalledProcessError as e:
    tag = 'v0.0.0'

version = tag[1:]

with open(os.path.join(project_dir, 'README.md'), 'r') as f:
    readme = f.read()


def run_and_log(cmd, **kwargs):
    sys.stderr.write('> {}\n'.format(' '.join(cmd)))
    return subprocess.call(cmd, **kwargs)


def translate_reqs(packages):
    re = importlib.import_module('re')
    tr = {
        'sklearn': 'scikit-learn',
        'codestyle': 'pycodestyle',
        # Apparently, there isn't mne-base on PyPI...
        'mne': 'mne-base',
    }
    result = []

    for p in packages:
        parts = re.split(r'[ <>=]', p, maxsplit=1)
        name = parts[0]
        version = p[len(name):]
        if name in tr:
            result.append(tr[name] + version)
        else:
            result.append(p)

    return result


class TestCommand(Command):

    user_options = [
        ('fast', 'f', (
            'Don\'t install dependencies, test in the current environment'
        )),
    ]

    def initialize_options(self):
        self.fast = False

    def finalize_options(self):
        self.test_args = []
        self.test_suite = True

    def sources(self):
        return glob(
            os.path.join(project_dir, '**/*.py'),
            recursive=True,
        ) + [os.path.join(project_dir, 'setup.py')]

    @contextmanager
    def prepare(self):
        tf = importlib.import_module('tempfile')
        venv = importlib.import_module('venv')

        class ContextVenvBuilder(venv.EnvBuilder):

            def ensure_directories(self, env_dir):
                self.context = super().ensure_directories(env_dir)
                return self.context

        recs = self.distribution.extras_require.get('tests', [])

        with tf.TemporaryDirectory() as builddir:
            vbuilder = ContextVenvBuilder(with_pip=True)
            vbuilder.create(os.path.join(builddir, '.venv'))
            env_python = vbuilder.context.env_exe

            # Install the package as a wheel
            subprocess.check_call([env_python, '-m', 'pip', 'install',
                                   '--upgrade', 'pip', 'setuptools', 'wheel'])
            subprocess.check_call([env_python, '-m', 'pip', 'install', '.'])

            # Install test dependencies
            if recs:
                subprocess.check_call(
                    [env_python, '-m', 'pip', 'install'] + recs)

            yield env_python

    def run(self):
        if not self.fast:
            with self.prepare() as env_python:
                self.run_tests(env_python)
        self.run_tests()


class UnitTest(TestCommand):

    description = 'run unit tests'

    def run_tests(self, env_python=None):
        unittest = importlib.import_module('unittest')
        if env_python is None:
            loader = unittest.TestLoader()
            suite = loader.discover('tests', pattern='test.py')
            runner = unittest.TextTestRunner()
            result = runner.run(suite)
            sys.exit(1 if result.errors else 0)

        tests = os.path.join(project_dir, 'tests', 'test.py')
        sys.exit(subprocess.call((env_python, '-m', 'unittest', tests)))


class Pep8(TestCommand):

    description = 'validate sources against PEP8'

    def run_tests(self, env_python=None):
        if env_python is None:
            from pycodestyle import StyleGuide

            style_guide = StyleGuide(paths=self.sources())
            options = style_guide.options

            report = style_guide.check_files()
            report.print_statistics()

            if report.total_errors:
                if options.count:
                    sys.stderr.write(str(report.total_errors) + '\n')
                sys.exit(1)
            sys.exit(0)

        sys.exit(
            subprocess.call(
                [env_python, '-m', 'pycodestyle'] + self.sources(),
            ))


class Isort(TestCommand):

    description = 'validate imports'

    def run_tests(self, env_python=None):
        options = ['-c', '--lai', '2', '-m' '3']

        if env_python is None:
            from isort.main import main as imain

            if imain(options + self.sources()):
                sys.exit(1)
            sys.exit(0)

        sys.exit(
            subprocess.call(
                [env_python, '-m', 'isort'] + options + self.sources(),
            ))


if __name__ == '__main__':
    setup(
        use_scm_version=True,
        long_description=open('README.md').read(),
        long_description_content_type="text/markdown",
        cmdclass={
            'test': UnitTest,
            'lint': Pep8,
            'isort': Isort,
        },
    )
