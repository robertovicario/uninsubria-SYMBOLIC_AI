"""Piccolo risolutore CSP per calendari d'esame, senza dipendenze esterne."""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter


ALGORITHMS = ("backtracking", "mrv", "mrv_fc")


@dataclass
class Stats:
    attempts: int = 0
    backtracks: int = 0
    pruned: int = 0
    seconds: float = 0.0


class SearchLimit(Exception):
    """Il limite di lavoro non permette di concludere la ricerca."""


def validate_input(data):
    slots = data["slots"]
    rooms = data["rooms"]
    exams = data["exams"]
    for label, ids in (("fasce", slots), ("aule", [r["id"] for r in rooms]),
                       ("esami", [e["id"] for e in exams])):
        if len(ids) != len(set(ids)):
            raise ValueError(f"Identificatori duplicati: {label}")
    for item in rooms + exams:
        if not set(item.get("available", slots)) <= set(slots):
            raise ValueError(f"Fascia sconosciuta in {item['id']}")
    for room in rooms:
        if not isinstance(room["capacity"], int) or room["capacity"] < 0:
            raise ValueError("La capienza deve essere un intero non negativo")
    for exam in exams:
        if not isinstance(exam["students"], int) or exam["students"] < 0:
            raise ValueError("Il numero di studenti deve essere un intero non negativo")
        if not isinstance(exam["teachers"], list) or not isinstance(exam["groups"], list):
            raise ValueError("teachers e groups devono essere liste")


def build_domains(data):
    """Applica una volta i vincoli unari: capienza e disponibilita'."""
    return {
        exam["id"]: [
            (slot, room["id"])
            for slot in data["slots"]
            for room in data["rooms"]
            if room["capacity"] >= exam["students"]
            and slot in room.get("available", data["slots"])
            and slot in exam.get("available", data["slots"])
        ]
        for exam in data["exams"]
    }


def compatible(exam_a, value_a, exam_b, value_b):
    """Ogni esame dura una fascia; fasce diverse non si sovrappongono."""
    if value_a[0] != value_b[0]:
        return True
    return (
        value_a[1] != value_b[1]
        and not set(exam_a["teachers"]) & set(exam_b["teachers"])
        and not set(exam_a["groups"]) & set(exam_b["groups"])
    )


def validate_solution(data, assignment):
    """Controllo indipendente dalla ricerca, con messaggi sui vincoli violati."""
    exams = data["exams"]
    rooms = {r["id"]: r for r in data["rooms"]}
    if set(assignment) != {e["id"] for e in exams}:
        raise ValueError("Calendario incompleto o con esami sconosciuti")
    for exam in exams:
        slot, room_id = assignment[exam["id"]]
        if slot not in data["slots"] or room_id not in rooms:
            raise ValueError("Aula o fascia sconosciuta")
        room = rooms[room_id]
        if room["capacity"] < exam["students"]:
            raise ValueError("Capienza insufficiente")
        if slot not in exam.get("available", data["slots"]):
            raise ValueError("Esame non disponibile")
        if slot not in room.get("available", data["slots"]):
            raise ValueError("Aula non disponibile")
    for i, a in enumerate(exams):
        for b in exams[i + 1:]:
            slot_a, room_a = assignment[a["id"]]
            slot_b, room_b = assignment[b["id"]]
            if slot_a == slot_b:
                if room_a == room_b:
                    raise ValueError("Aula occupata da due esami")
                if set(a["teachers"]).intersection(b["teachers"]):
                    raise ValueError("Sovrapposizione docenti")
                if set(a["groups"]).intersection(b["groups"]):
                    raise ValueError("Sovrapposizione studenti")


def solve(data, algorithm="mrv_fc", max_attempts=1_000_000):
    """Restituisce (soluzione, statistiche, esito); None non implica impossibilita'."""
    validate_input(data)
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Algoritmo sconosciuto: {algorithm}")
    if max_attempts < 1:
        raise ValueError("max_attempts deve essere positivo")
    exams = {e["id"]: e for e in data["exams"]}
    stats = Stats()
    assignment = {}

    def allowed(name, value):
        return all(compatible(exams[name], value, exams[other], chosen)
                   for other, chosen in assignment.items())

    def search(domains):
        if len(assignment) == len(exams):
            return dict(assignment)
        pending = [name for name in exams if name not in assignment]
        if algorithm == "backtracking":
            name = pending[0]
        else:
            # MRV conta valori compatibili anche senza forward checking.
            # A parita' di dominio si conserva l'ordine dell'input.
            name = min(pending, key=lambda n: sum(allowed(n, v) for v in domains[n]))
        for value in domains[name]:
            if stats.attempts >= max_attempts:
                raise SearchLimit
            stats.attempts += 1
            if not allowed(name, value):
                continue
            assignment[name] = value
            next_domains = domains
            dead_end = False
            if algorithm == "mrv_fc":
                next_domains = dict(domains)
                for other in pending:
                    if other == name:
                        continue
                    kept = [v for v in domains[other]
                            if compatible(exams[name], value, exams[other], v)]
                    stats.pruned += len(domains[other]) - len(kept)
                    next_domains[other] = kept
                    if not kept:
                        dead_end = True
                        break
            if not dead_end:
                result = search(next_domains)
                if result is not None:
                    return result
            del assignment[name]
            # Numero di assegnazioni compatibili annullate.
            stats.backtracks += 1
        return None

    started = perf_counter()
    try:
        domains = build_domains(data)
        solution = None if any(not d for d in domains.values()) else search(domains)
        status = "risolto" if solution is not None else "impossibile"
    except SearchLimit:
        solution, status = None, "limite raggiunto"
    stats.seconds = perf_counter() - started
    if solution is not None:
        validate_solution(data, solution)
    return solution, stats, status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance", nargs="?", type=Path,
                        default=Path(__file__).with_name("example.json"))
    parser.add_argument("--algorithm", choices=("all",) + ALGORITHMS, default="all")
    parser.add_argument("--max-attempts", type=int, default=1_000_000)
    parser.add_argument("--impossible", action="store_true",
                        help="Forza tutti gli esami nella prima fascia")
    args = parser.parse_args()
    data = json.loads(args.instance.read_text(encoding="utf-8"))
    if args.impossible:
        for exam in data["exams"]:
            exam["available"] = data["slots"][:1]
    algorithms = ALGORITHMS if args.algorithm == "all" else (args.algorithm,)
    print(f"Esami: {len(data['exams'])} | Aule: {len(data['rooms'])} | Fasce: {len(data['slots'])}")
    print(f"{'Algoritmo':<16} {'Esito':<18} {'Tentativi':>10} {'Backtrack':>10} {'Potature':>10} {'ms':>10}")
    for algorithm in algorithms:
        solution, stats, status = solve(data, algorithm, args.max_attempts)
        print(f"{algorithm:<16} {status:<18} {stats.attempts:>10} {stats.backtracks:>10} "
              f"{stats.pruned:>10} {stats.seconds * 1000:>10.3f}")
        if solution is not None:
            print("  Calendario verificato:")
            for slot in data["slots"]:
                for exam in data["exams"]:
                    chosen_slot, room = solution[exam["id"]]
                    if chosen_slot == slot:
                        print(f"    {slot:<12} {room:<8} {exam['id']}")


if __name__ == "__main__":
    main()
