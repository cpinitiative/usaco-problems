import axios from 'axios';
import { writeFileSync } from 'fs';

export type Sample = {
  input: string;
  output: string;
};

export type ProblemData = {
  id: number;
  url: string;
  source: {
    sourceString: string;
    year: number;
    contest: string;
    division: string;
  };
  submittable: boolean;
  title: {
    titleString: string;
    place: number;
    name: string;
  };
  input: string;
  output: string;
  samples: Sample[];
};

const problems = require('./problems.json') as { [key: string]: ProblemData };
let report = 'added problems:\n```\n';

async function addProblem(id: number) {
  console.log('Adding problem', id);
  try {
    const url = `http://usaco.org/index.php?page=viewproblem2&cpid=${id}`;
    const response = await axios.get(url);
    const htmlContent: string = response.data;
    const problem = htmlContent.match(/<h2> Problem (\d). (.*) <\/h2>/)!;
    const number = problem[1],
      title = problem[2];
    const contest = htmlContent.match(
      /<h2> USACO (\d+) (December|January|February|(?:US Open)) Contest, (Bronze|Silver|Gold|Platinum) <\/h2>/
    )!;
    const year = contest[1],
      month = contest[2],
      division = contest[3];
    const sample_input = /<h4>SAMPLE INPUT:<\/h4>\s*<pre class='in'>\n?([\w\W]*?)<\/pre>/g;
    const sample_output = /<h4>SAMPLE OUTPUT:<\/h4>\s*<pre class='out'>\n?([\w\W]*?)<\/pre>/g;
    const inputs = [...htmlContent.matchAll(sample_input)!].map(match => match[1]);
    const outputs = [...htmlContent.matchAll(sample_output)!].map(match => match[1]);
    console.log('Problem', number, title, year, month, division);
    problems[id] = {
      id: id,
      url: `http://www.usaco.org/index.php?page=viewproblem2&cpid=${id}`,
      source: {
        sourceString: `${year} ${month} ${division}`,
        year: +year,
        contest: month,
        division: division
      },
      submittable: true,
      title: {
        titleString: `${number}. ${title}`,
        place: +number,
        name: title
      },
      input: "stdin",
      output: "stdout",
      samples: inputs.map((input, i) => ({
        input: input,
        output: outputs[i],
      })),
    };
    console.log('Problem added!');
    report += `id ${id}: ${problems[id].title.name} (#${problems[id].title.place} from ${problems[id].source.sourceString})\n`;
    return true;
  } catch (error) {
    console.log('Invalid problem id!');
    return false;
  }
}

// max id gap between two consecutive contests
(async () => {
  const MAX_GAP = 20;
  const LAST_ID = Math.max(...Object.keys(problems).map(Number));
  let id = LAST_ID + 1;
  while (!await addProblem(id++)) {
    if (id - LAST_ID > MAX_GAP) {
      console.log('No more problems to add!');
      process.exit(0);
    }
  }
  while (await addProblem(id++));
  report += '```';
  writeFileSync(
    'problems.json', 
    JSON.stringify(problems, null, 2)
  );
  writeFileSync(
    'out/report.txt',
    report
  );
  process.exit(1);
})();