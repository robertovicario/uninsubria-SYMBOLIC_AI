"""Verifiche dei solver rispetto a enumerazione esaustiva su piccoli CSP."""

import itertools
import json
from pathlib import Path
import random
import unittest

from scheduler import ALGORITHMS, solve, validate_solution


class SchedulerTests(unittest.TestCase):
    def test_example_and_impossible(self):
        data = json.loads(Path(__file__).with_name("example.json").read_text())
        for algorithm in ALGORITHMS:
            solution, _, status = solve(data, algorithm)
            self.assertEqual(status, "risolto")
            validate_solution(data, solution)
        for exam in data["exams"]:
            exam["available"] = data["slots"][:1]
        for algorithm in ALGORITHMS:
            self.assertEqual(solve(data, algorithm)[2], "impossibile")

    def test_exhaustive_reference(self):
        rng = random.Random(42)
        for case in range(40):
            data = {
                "slots": ["S1", "S2"],
                "rooms": [{"id": "A", "capacity": 20}, {"id": "B", "capacity": 40}],
                "exams": [
                    {"id": str(i), "students": rng.choice([10, 30, 50]),
                     "teachers": [str(rng.randrange(3))],
                     "groups": [str(rng.randrange(3))],
                     "available": rng.choice([["S1"], ["S2"], ["S1", "S2"], []])}
                    for i in range(4)
                ],
            }
            # Enumera anche valori che violano capienza/disponibilita':
            # il verificatore decide se ciascun calendario completo e' valido.
            exists = False
            values = list(itertools.product(data["slots"], ["A", "B"]))
            for choices in itertools.product(values, repeat=4):
                try:
                    validate_solution(data, dict(zip(["0", "1", "2", "3"], choices)))
                except ValueError:
                    continue
                exists = True
                break
            for algorithm in ALGORITHMS:
                with self.subTest(case=case, algorithm=algorithm):
                    solution, _, status = solve(data, algorithm)
                    self.assertEqual(status, "risolto" if exists else "impossibile")
                    if solution is not None:
                        validate_solution(data, solution)

    def test_limit_is_not_unsatisfiability(self):
        data = json.loads(Path(__file__).with_name("example.json").read_text())
        for algorithm in ALGORITHMS:
            self.assertEqual(solve(data, algorithm, max_attempts=1)[2], "limite raggiunto")

    def test_validator_rejects_conflicts(self):
        data = {"slots": ["S"], "rooms": [{"id": "A", "capacity": 10},
                                                {"id": "B", "capacity": 10}],
                "exams": [{"id": "X", "students": 5, "teachers": ["T"], "groups": []},
                          {"id": "Y", "students": 5, "teachers": ["T"], "groups": []}]}
        with self.assertRaises(ValueError):
            validate_solution(data, {"X": ("S", "A"), "Y": ("S", "B")})
        data["exams"][1]["teachers"] = []
        data["exams"][0]["groups"] = data["exams"][1]["groups"] = ["G"]
        with self.assertRaises(ValueError):
            validate_solution(data, {"X": ("S", "A"), "Y": ("S", "B")})


if __name__ == "__main__":
    unittest.main()
