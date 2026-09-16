"""Check command boundaries without Docker or network access."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class BookCommandsTest(unittest.TestCase):
    def setUp(self):
        temp_root = REPO / '.tmp' / 'book-playgrounds'
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_root)
        self.base = Path(self.temp.name)
        self.book = self.base / 'book with spaces'
        self.book.mkdir()
        (self.base / 'scripts').symlink_to(REPO / 'scripts', target_is_directory=True)
        for name in ('code', 'exercises', '.state'):
            (self.book / name).mkdir()
        (self.book / 'Dockerfile').touch()
        (self.book / 'mise.toml').write_text((REPO / 'build_a_large_language_model_from_scratch/mise.toml').read_text())
        (self.book / 'book.env').write_text('BOOK_KIND=llm\nBOOK_IMAGE=local/test\nAUTHOR_URL=unused\nAUTHOR_REVISION=0000000000000000000000000000000000000000\n')
        self.log = self.base / 'docker.jsonl'
        binary = self.base / 'bin'
        binary.mkdir()
        docker = binary / 'docker'
        docker.write_text(f'''#!{sys.executable}
import json, os, sys

args = sys.argv[1:]
with open(os.environ["DOCKER_TEST_LOG"], "a") as f:
    f.write(json.dumps(args) + "\\n")
if os.environ.get("DOCKER_TEST_MISSING") and args[:2] == ["image", "inspect"]:
    sys.exit(1)
if args and args[0] == "run":
    probe = any("import signal" in arg for arg in args)
    if probe and os.environ.get("DOCKER_TEST_GPU") == "fail":
        sys.exit(1)
    if not probe and os.environ.get("DOCKER_TEST_JOB") == "fail":
        sys.exit(1)
''')
        docker.chmod(0o755)
        self.env = dict(os.environ, MISE_CONFIG_ROOT=str(self.book),
                        PATH=str(binary) + os.pathsep + os.environ['PATH'], DOCKER_TEST_LOG=str(self.log),
                        MISE_TRUSTED_CONFIG_PATHS=str(self.book))
        self.env.pop('BOOK_GPU', None)

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args, **env):
        return subprocess.run(['bash', str(REPO / 'scripts/python-book.sh'), *args],
                              env=dict(self.env, **env), cwd=self.book, capture_output=True, text=True)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def run_calls(self):
        return [call for call in self.calls() if call and call[0] == 'run']

    @staticmethod
    def env_value(call, name):
        return next(call[i + 1] for i, arg in enumerate(call[:-1])
                    if arg == '--env' and call[i + 1].startswith(name + '='))

    def test_script_arguments_and_spaces_survive(self):
        (self.book / 'exercises' / 'my work.py').touch()
        result = self.command('run', 'exercises/my work.py', 'two words', '$(false)')
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(calls[-1][-4:], ['/workspace/exercises', 'my work.py', 'two words', '$(false)'])

    def test_outside_paths_never_reach_docker(self):
        (self.book / 'exercises' / 'outside').symlink_to(self.base, target_is_directory=True)
        for path in ('/etc/passwd', 'code/../../file.py', 'exercises/outside/file.py', ''):
            with self.subTest(path=path):
                result = self.command('run', path)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.log.exists())

    def test_mise_forwards_script_arguments(self):
        (self.book / 'exercises' / 'work.py').touch()
        result = subprocess.run(['mise', 'run', 'run', '--', 'exercises/work.py', 'two words'],
                                env=self.env, cwd=self.book, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(calls[-1][-3:], ['/workspace/exercises', 'work.py', 'two words'])

    def test_build_uses_absolute_context(self):
        result = subprocess.run(['bash', str(REPO / 'scripts/book-container.sh'), 'setup', 'local/test'],
                                env=self.env, cwd=self.book, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(calls[-1][-1], str(self.book))

    def test_missing_file_never_reaches_docker(self):
        self.assertNotEqual(self.command('run', 'exercises/missing.py').returncode, 0)
        self.assertFalse(self.log.exists())

    def test_reference_tests_are_not_reported_as_learner_tests(self):
        self.assertNotEqual(self.command('test', 'code').returncode, 0)
        self.assertFalse(self.log.exists())

    def test_invalid_port_rejected_before_container_run(self):
        result = self.command('lab', BOOK_PORT='8888:80')
        self.assertNotEqual(result.returncode, 0)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertFalse(any(call[0] == 'run' for call in calls))

    def test_doctor_rejects_wrong_reference_revision(self):
        subprocess.run(['git', 'init', '-q', str(self.book / 'code')], check=True)
        subprocess.run(['git', '-C', str(self.book / 'code'), '-c', 'user.name=Test',
                        '-c', 'user.email=test@example.invalid', 'commit', '-q', '--allow-empty', '-m', 'fixture'], check=True)
        result = self.command('doctor')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Author revision differs', result.stderr)
        self.assertFalse(self.log.exists())

    def test_service_configuration_reaches_docker(self):
        env_file = self.book / '.state' / 'services.env'
        env_file.write_text('TEST_VALUE=fixture\n')
        result = self.command('shell', BOOK_ENV_FILE=str(env_file), BOOK_NETWORK='ml-book-services', BOOK_MEMORY='20g')
        self.assertEqual(result.returncode, 0, result.stderr)
        call = json.loads(self.log.read_text().splitlines()[-1])
        for flag, value in [('--env-file', str(env_file)), ('--network', 'ml-book-services')]:
            self.assertEqual(call[call.index(flag) + 1], value)
        self.assertIn('--memory=20g', call)

    def test_fetch_preserves_existing_non_git_work(self):
        work = self.book / 'code' / 'work.py'
        work.write_text('preserve this work\n')
        result = self.command('fetch')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(work.read_text(), 'preserve this work\n')
        self.assertFalse((self.book / 'code' / '.git').exists())

    def test_editor_uses_book_image_and_only_book_mounts(self):
        result = self.command('edit', 'exercises/new notebook.ipynb', BOOK_GPU='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        call = self.calls()[-1]
        self.assertIn('local/test-editor', call)
        self.assertEqual(call[-1], '/workspace/exercises/new notebook.ipynb')
        self.assertIn('--gpus', call)
        mounts = [call[i + 1] for i, arg in enumerate(call) if arg == '--mount']
        book_mounts = [mount for mount in mounts if not mount.startswith('type=bind,src=/dev/nvidia-')]
        self.assertTrue(all(f'src={self.book}/' in mount for mount in book_mounts))
        expected_devices = [device for device in ('/dev/nvidia-uvm', '/dev/nvidia-uvm-tools')
                            if Path(device).is_char_device()]
        self.assertEqual([mount for mount in mounts if mount.startswith('type=bind,src=/dev/nvidia-')],
                         [f'type=bind,src={device},dst={device}' for device in expected_devices])
        self.assertEqual([call[i + 1] for i, arg in enumerate(call[:-1])
                          if arg == '--device' and call[i + 1].startswith('/dev/nvidia-')], expected_devices)
        self.assertFalse(any('.config/nvim' in mount or 'docker.sock' in mount for mount in mounts))

    def test_auto_gpu_preflight_selects_gpu_for_the_actual_job(self):
        result = self.command('shell')
        self.assertEqual(result.returncode, 0, result.stderr)
        runs = self.run_calls()
        self.assertEqual(len(runs), 2)
        probe, job = runs
        self.assertTrue(any('import signal' in arg for arg in probe))
        self.assertFalse(any('import signal' in arg for arg in job))
        expected_devices = [device for device in ('/dev/nvidia-uvm', '/dev/nvidia-uvm-tools')
                            if Path(device).is_char_device()]
        for call in runs:
            self.assertIn('--gpus', call)
            self.assertEqual([call[i + 1] for i, arg in enumerate(call[:-1])
                              if arg == '--device' and call[i + 1].startswith('/dev/nvidia-')], expected_devices)
            self.assertEqual([call[i + 1] for i, arg in enumerate(call[:-1])
                              if arg == '--mount' and call[i + 1].startswith('type=bind,src=/dev/nvidia-')],
                             [f'type=bind,src={device},dst={device}' for device in expected_devices])
        self.assertEqual(self.env_value(job, 'BOOK_GPU'), 'BOOK_GPU=1')

    def test_auto_gpu_failure_runs_cpu_once(self):
        result = self.command('shell', DOCKER_TEST_GPU='fail')
        self.assertEqual(result.returncode, 0, result.stderr)
        runs = self.run_calls()
        self.assertEqual(len(runs), 2)
        probe, job = runs
        self.assertTrue(any('import signal' in arg for arg in probe))
        self.assertFalse(any('import signal' in arg for arg in job))
        self.assertNotIn('--gpus', job)
        self.assertNotIn('/dev/nvidia-uvm', job)
        self.assertEqual(self.env_value(job, 'BOOK_GPU'), 'BOOK_GPU=0')
        self.assertIn('CUDA_VISIBLE_DEVICES=-1', job)
        self.assertIn('NVIDIA_VISIBLE_DEVICES=void', job)
        self.assertIn('JAX_PLATFORMS=cpu', job)

    def test_strict_gpu_failure_stops_before_actual_job(self):
        result = self.command('shell', BOOK_GPU='1', DOCKER_TEST_GPU='fail')
        self.assertNotEqual(result.returncode, 0)
        runs = self.run_calls()
        self.assertEqual(len(runs), 1)
        self.assertTrue(any('import signal' in arg for arg in runs[0]))

    def test_explicit_cpu_skips_gpu_preflight(self):
        result = self.command('shell', BOOK_GPU='0', DOCKER_TEST_GPU='fail')
        self.assertEqual(result.returncode, 0, result.stderr)
        runs = self.run_calls()
        self.assertEqual(len(runs), 1)
        self.assertFalse(any('import signal' in arg for arg in runs[0]))
        self.assertNotIn('--gpus', runs[0])
        self.assertEqual(self.env_value(runs[0], 'BOOK_GPU'), 'BOOK_GPU=0')

    def test_invalid_gpu_mode_fails_before_container_run(self):
        result = self.command('shell', BOOK_GPU='maybe')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.run_calls(), [])

    def test_actual_gpu_job_failure_is_not_retried_on_cpu(self):
        result = self.command('shell', DOCKER_TEST_JOB='fail')
        self.assertNotEqual(result.returncode, 0)
        runs = self.run_calls()
        self.assertEqual(len(runs), 2)
        self.assertTrue(any('import signal' in arg for arg in runs[0]))
        self.assertFalse(any('import signal' in arg for arg in runs[1]))
        self.assertIn('--gpus', runs[1])
        self.assertEqual(self.env_value(runs[1], 'BOOK_GPU'), 'BOOK_GPU=1')

    def test_paper_workdir_runs_without_dockerfile_but_setup_still_requires_one(self):
        runner = REPO / 'scripts' / 'book-container.sh'
        (self.book / 'Dockerfile').unlink()
        command = ['bash', str(runner), 'run', 'local/test', 'python', '-c', 'print("paper")']
        with self.subTest('run'):
            result = subprocess.run(command, env=self.env, cwd=self.book, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            runs = self.run_calls()
            self.assertEqual(len(runs), 2)
            self.assertTrue(any('import signal' in arg for arg in runs[0]))
            self.assertEqual(runs[1][-4:], ['local/test', 'python', '-c', 'print("paper")'])
            self.assertEqual(self.env_value(runs[1], 'BOOK_GPU'), 'BOOK_GPU=1')
        before_setup = self.calls()
        with self.subTest('setup'):
            result = subprocess.run(['bash', str(runner), 'setup', 'local/test'],
                                    env=self.env, cwd=self.book, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.calls(), before_setup)

    def test_editor_rejects_escape_reference_and_extra_arguments(self):
        (self.book / 'exercises' / 'outside').symlink_to(self.base, target_is_directory=True)
        for args in [('code/example.ipynb',), ('exercises/outside/file.py',),
                     ('exercises/missing/file.py',), ('exercises/file.py', '--cmd', 'quit')]:
            with self.subTest(args=args):
                self.assertNotEqual(self.command('edit', *args).returncode, 0)
                self.assertFalse(self.log.exists())

    def test_missing_editor_image_points_to_editor_setup(self):
        result = self.command('edit', 'exercises/new.py', DOCKER_TEST_MISSING='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('mise run editor:setup', result.stderr)

    def test_editor_snapshot_is_atomic_preserves_config_and_excludes_private_files(self):
        config = self.base / 'config' / 'nvim'
        data = self.base / 'data' / 'nvim'
        config.mkdir(parents=True)
        (data / 'lazy/lazy.nvim').mkdir(parents=True)
        (config / 'init.lua').write_text('-- existing config\n')
        (config / '.env').write_text('PRIVATE_TOKEN=fixture\n')
        secret = self.base / 'private.txt'
        secret.write_text('private fixture\n')
        (config / 'escape.lua').symlink_to(secret)
        target = self.book / '.state/editor'
        command = [sys.executable, str(REPO / 'scripts/editor/snapshot.py'), str(target)]
        env = dict(self.env, HOME=str(self.base), XDG_CONFIG_HOME=str(config.parent), XDG_DATA_HOME=str(data.parent))
        failed = subprocess.run(command, env=env, capture_output=True, text=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertFalse((target / 'config/nvim').exists())
        (config / 'escape.lua').unlink()
        subprocess.run(command, env=env, check=True, capture_output=True)
        self.assertFalse((target / 'config/nvim/.env').exists())
        self.assertEqual((target / 'config/nvim/init.lua').read_text(), '-- existing config\n')
        (config / 'init.lua').write_text('-- changed on host\n')
        subprocess.run(command, env=env, check=True, capture_output=True)
        self.assertEqual((target / 'config/nvim/init.lua').read_text(), '-- existing config\n')


if __name__ == '__main__':
    unittest.main()
