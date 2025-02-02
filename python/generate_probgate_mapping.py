#!/usr/bin/env python3

import json
import re
import os
from typing import Dict, List, TypedDict, Optional


class ProbgateContest(TypedDict):
    contest_id: str
    name: str
    month: str
    year: str
    division: str
    problems: List[Dict[str, str]]


class UsacoProblem(TypedDict):
    id: int
    source: Dict[str, str]
    title: Dict[str, str]


def normalize_month(month: str) -> str:
    """Normalize month names between USACO and Probgate formats."""
    month_map = {
        "January": "JAN",
        "February": "FEB",
        "March": "MAR",
        "April": "APR",
        "December": "DEC",
        "US Open": "OPEN",
        "November": "NOV",
    }
    return month_map.get(month, month)


def normalize_year(year: str) -> str:
    """Normalize year format between USACO and Probgate formats."""
    if len(year) == 2:
        return "20" + year
    return year


def clean_problem_name(name: str) -> str:
    """Clean problem name by removing division indicators and suffixes."""
    # Remove division indicators in brackets/parentheses
    name = re.sub(r'\s*[\[\(](Bronze|Silver|Gold|Platinum|bronze|silver|gold|platinum)[\]\)]\s*', '', name)
    
    # Remove suffixes like "Easier" and "Harder"
    name = re.sub(r'\s*\((Easier|Harder|New Version|Old Tests|New Tests)\)\s*', '', name)
    
    return name.strip().lower()


def get_manual_match(
    probgate_problem: Dict[str, str],
    probgate_contest: ProbgateContest,
) -> Optional[str]:
    """Handle edge cases that need manual matching."""
    # Map of (probgate_name, month, year, division) -> usaco_id
    manual_matches = {
        ("Photoshoot 3", "OPEN", "2022", "Bronze"): "1346",  # Photoshoot 3
        ("Hoof Paper Scissors", "JAN", "2017", "Bronze"): "688",  # Hoof, Paper, Scissors
        ("Marathon Cheating (Bronze)", "DEC", "2014", "Bronze"): "494",  # Marathon
    }
    
    key = (
        probgate_problem["name"],
        probgate_contest["month"],
        normalize_year(probgate_contest["year"]),
        probgate_contest["division"]
    )
    return manual_matches.get(key)


def find_matching_usaco_problem(
    probgate_problem: Dict[str, str],
    probgate_contest: ProbgateContest,
    usaco_problems: Dict[str, UsacoProblem],
) -> Optional[str]:
    """Find matching USACO problem ID for a Probgate problem."""
    # First check manual matches
    manual_match = get_manual_match(probgate_problem, probgate_contest)
    if manual_match:
        return manual_match
        
    probgate_name = clean_problem_name(probgate_problem["name"])
    probgate_year = normalize_year(probgate_contest["year"])
    
    # Debug output for the first few problems
    if probgate_name.startswith("roundabout"):
        print(f"\nLooking for problem: {probgate_name}")
        print(f"Contest: {probgate_contest['month']} {probgate_year} {probgate_contest['division']}")
        
        # Print first few USACO problems that match the month/year/division
        count = 0
        for usaco_id, usaco_problem in usaco_problems.items():
            if (normalize_month(usaco_problem["source"]["contest"]) == probgate_contest["month"]
                and str(usaco_problem["source"]["year"]) == probgate_year
                and usaco_problem["source"]["division"] == probgate_contest["division"]):
                print(f"Potential match: {clean_problem_name(usaco_problem['title']['name'])}")
                count += 1
                if count >= 5:
                    break
    
    for usaco_id, usaco_problem in usaco_problems.items():
        usaco_name = clean_problem_name(usaco_problem["title"]["name"])
        if (
            probgate_name in usaco_name
            and normalize_month(usaco_problem["source"]["contest"]) == probgate_contest["month"]
            and str(usaco_problem["source"]["year"]) == probgate_year
            and usaco_problem["source"]["division"] == probgate_contest["division"]
        ):
            return usaco_id
    return None


def main():
    """Generate mapping between USACO and Probgate problems."""
    # Load USACO problems
    with open("data_private/usaco/problems.json", "r") as f:
        usaco_problems = json.load(f)
    
    # Load Probgate contests and problems
    with open("data_private/probgate/contests.json", "r") as f:
        probgate_contests = json.load(f)
    
    # Initialize mapping
    mapping = {}
    errors = []
    
    # Process each contest
    for contest in probgate_contests:
        for problem in contest["problems"]:
            usaco_id = find_matching_usaco_problem(problem, contest, usaco_problems)
            if usaco_id:
                mapping[usaco_id] = problem["problem_id"]  # Use problem_id instead of id
            else:
                errors.append(f"Could not find matching USACO problem for Probgate problem: {problem['name']} ({contest['month']}{contest['year']} {contest['division']}, ID: {problem['problem_id']})")
    
    # Save mapping to file
    os.makedirs("data_private/probgate", exist_ok=True)
    with open("data_private/probgate/usaco_to_probgate_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nGenerated mapping for {len(mapping)} problems")
    print(f"Found {len(errors)} errors")
    for error in errors:
        print(error)


if __name__ == "__main__":
    import sys
    main()
