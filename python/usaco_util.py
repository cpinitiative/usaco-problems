import json
import re
import sys
from typing import Dict, List, TypedDict
import requests


class Sample(TypedDict):
    input: str
    output: str


class Source(TypedDict):
    sourceString: str
    year: int
    contest: str
    division: str


class Title(TypedDict):
    titleString: str
    place: int
    name: str


class ProblemData(TypedDict):
    id: int
    url: str
    source: Source
    submittable: bool
    title: Title
    input: str
    output: str
    samples: List[Sample]


def add_problem(problem_id: int, problems: Dict[str, ProblemData]) -> bool:
    """
    Scrapes a USACO problem with the given ID and adds it to the problems dictionary.
    Returns True if the problem was successfully added, False otherwise.
    """
    try:
        url = f"https://usaco.org/index.php?page=viewproblem2&cpid={problem_id}"
        response = requests.get(url)
        html_content = response.text

        # Extract problem title and number
        problem_match = re.search(r'<h2> Problem (\d). (.*?) </h2>', html_content)
        if not problem_match:
            return False
        number, title = problem_match.groups()

        # Extract contest info
        contest_match = re.search(
            r'<h2> USACO (\d+) (December|January|February|US Open) Contest, (Bronze|Silver|Gold|Platinum) </h2>',
            html_content
        )
        if not contest_match:
            return False
        year, month, division = contest_match.groups()

        # Extract sample inputs and outputs
        sample_input_pattern = r'<h4>SAMPLE INPUT:</h4>\s*<pre class=\'in\'>\n?([\w\W]*?)</pre>'
        sample_output_pattern = r'<h4>SAMPLE OUTPUT:</h4>\s*<pre class=\'out\'>\n?([\w\W]*?)</pre>'
        
        inputs = [match.group(1) for match in re.finditer(sample_input_pattern, html_content)]
        outputs = [match.group(1) for match in re.finditer(sample_output_pattern, html_content)]

        # Create problem data
        problem_data: ProblemData = {
            "id": problem_id,
            "url": url,
            "source": {
                "sourceString": f"{year} {month} {division}",
                "year": int(year),
                "contest": month,
                "division": division,
            },
            "submittable": True,
            "title": {
                "titleString": f"{number}. {title}",
                "place": int(number),
                "name": title,
            },
            "input": "stdin",
            "output": "stdout",
            "samples": [
                {"input": input_text, "output": output_text}
                for input_text, output_text in zip(inputs, outputs)
            ],
        }

        problems[str(problem_id)] = problem_data
        print(f"id {problem_id}: {problem_data['title']['name']} (#{problem_data['title']['place']} from {problem_data['source']['sourceString']})")
        return True

    except Exception as e:
        if not isinstance(e, TypeError):
            print(f"Error processing problem {problem_id}: {str(e)}", file=sys.stderr)
        return False


def main():
    # Load existing problems
    with open('problems.json', 'r') as f:
        problems = json.load(f)

    # Maximum gap between consecutive contest IDs
    MAX_GAP = 20
    LAST_ID = max(int(id_) for id_ in problems.keys())
    
    last_added = LAST_ID
    current_id = last_added + 1
    
    # Keep trying new IDs until we hit a gap of MAX_GAP with no valid problems
    while current_id - last_added < MAX_GAP:
        if add_problem(current_id, problems):
            last_added = current_id
        current_id += 1

    # If we found new problems, save the updated problems.json
    if last_added > LAST_ID:
        with open('problems.json', 'w') as f:
            json.dump(problems, f, indent=2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
