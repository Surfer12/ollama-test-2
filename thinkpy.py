import unittest
from thinkjava import Thought, Log
from dataclasses import dataclass
from functools import total_ordering

@total_ordering
@dataclass
class MyThought:
    thought: str

    def __lt__(self, other):
        if isinstance(other, MyThought):
            return self.thought < other.thought
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, MyThought):
            return self.thought == other.thought
        return NotImplemented

class TestThink(unittest.TestCase):

    def test_think(self):
        log = Log()
        thought1 = "This is a complex thought that requires reasoning."
        thought2 = "This is another thought that builds on the previous one."

        log.think(thought1)
        log.think(thought2)

        self.assertEqual(len(log.log), 2)
        self.assertEqual(log.log[0], Thought(thought1))
        self.assertEqual(log.log[1], Thought(thought2))

    def test_better_compare_for_dataclass(self):
        thought1 = MyThought("This is a complex thought that requires reasoning.")
        thought2 = MyThought("This is another thought that builds on the previous one.")
        thought3 = "This is a simple thought."

        self.assertTrue(thought1 < thought2)
        self.assertTrue(thought2 > thought1)
        self.assertTrue(thought1 > thought3)
        self.assertTrue(thought3 < thought1)

if __name__ == '__main__':
    unittest.main()
