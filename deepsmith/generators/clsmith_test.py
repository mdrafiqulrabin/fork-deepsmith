"""Unit tests for //deeplearning/deepsmith/generators/clsmith.py."""
import os
import sys
import tempfile

import pytest
from absl import app
from absl import flags

from deeplearning.deepsmith.generators import clsmith
from deeplearning.deepsmith.proto import deepsmith_pb2
from deeplearning.deepsmith.proto import generator_pb2


FLAGS = flags.FLAGS


@pytest.fixture(scope='function')
def abc_config() -> generator_pb2.ClsmithGenerator:
  return generator_pb2.ClsmithGenerator(
      testcase_skeleton=[
        deepsmith_pb2.Testcase(
            toolchain='opencl',
            inputs={
              'gsize': '1,1,1',
              'lsize': '1,1,1',
            },
            harness=deepsmith_pb2.Harness(name='cl_launcher')
        ),
        deepsmith_pb2.Testcase(
            toolchain='opencl',
            inputs={
              'gsize': '128,16,1',
              'lsize': '8,4,1',
            },
            harness=deepsmith_pb2.Harness(name='cl_launcher')
        ),
      ]
  )


@pytest.fixture(scope='function')
def abc_generator(
    abc_config: generator_pb2.ClsmithGenerator) -> clsmith.ClsmithGenerator:
  return clsmith.ClsmithGenerator(abc_config)


def test_ClsmithGenerator_GenerateOneSource(
    abc_generator: clsmith.ClsmithGenerator):
  """Test that CLSmith generates a source file."""
  with tempfile.TemporaryDirectory(prefix='clsmith_') as d:
    os.chdir(d)
    src, wall_time, start_time = abc_generator.GenerateOneSource()
    # Check the basic structure of the generated file.
    assert src.startswith('// -g ')
    assert 'kernel void ' in src
    # We don't check the actual values, just the types.
    assert isinstance(wall_time, int)
    assert wall_time
    assert isinstance(start_time, int)
    assert start_time


def test_ClsmithGenerator_GenerateTestcases(
    abc_generator: clsmith.ClsmithGenerator):
  """End-to-end test of testcase generation."""
  req = generator_pb2.GenerateTestcasesRequest(num_testcases=10)
  res = abc_generator.GenerateTestcases(req, None)
  assert len(res.testcases) == 10
  for i in range(0, 10, 2):
    assert res.testcases[i].inputs['gsize'] == '1,1,1'
    assert res.testcases[i + 1].inputs['gsize'] == '128,16,1'
    assert res.testcases[i].inputs['lsize'] == '1,1,1'
    assert res.testcases[i + 1].inputs['lsize'] == '8,4,1'
    assert res.testcases[i].inputs['src'] == res.testcases[i + 1].inputs['src']
  # It is unlikely that the same program is generated 10 times, but this is
  # technically flaky.
  assert (res.testcases[0].inputs['src'] !=
          res.testcases[2].inputs['src'] !=
          res.testcases[4].inputs['src'] !=
          res.testcases[6].inputs['src'] !=
          res.testcases[8].inputs['src'])


def main(argv):
  """Main entry point."""
  if len(argv) > 1:
    raise app.UsageError("Unknown arguments: '{}'.".format(' '.join(argv[1:])))
  sys.exit(pytest.main([__file__, '-vv']))


if __name__ == '__main__':
  flags.FLAGS(['argv[0]', '-v=1'])
  app.run(main)
