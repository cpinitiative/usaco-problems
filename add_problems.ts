import {
  createWriteStream,
  mkdirSync,
  readdirSync,
  readFileSync,
  writeFileSync,
} from 'fs';
import * as prettier from 'prettier';
import { ProblemData } from './ProblemData';

process.chdir(__dirname);
const ids = readFileSync('../ids.log').toString().split('\n');
const EXTRAPROBLEMS_PATH = '../content/extraProblems.json';
const extraProblems = require(EXTRAPROBLEMS_PATH);
const DIVTOPROBS_PATH =
  '../src/components/markdown/ProblemsList/DivisionList/div_to_probs.json';
const div_to_probs = require(DIVTOPROBS_PATH);
const IDTOSOL_PATH =
  '../src/components/markdown/ProblemsList/DivisionList/id_to_sol.json';
const id_to_sol = require(IDTOSOL_PATH);
const problems = require('./problems.json') as { [key: string]: ProblemData };
if (!readdirSync('.').find(x => x == 'out')) mkdirSync('out');
const report = createWriteStream('out/report.txt');
report.write('added problems:\n```\n');
for (const id in problems) {
  if (id == '742') continue; // modern art :(
  if (!ids.find(x => x == `usaco-${id}`)) {
    extraProblems.EXTRA_PROBLEMS.push({
      uniqueId: `usaco-${id}`,
      name: problems[id].title.name,
      url: problems[id].url,
      source: problems[id].source.division,
      difficulty: 'N/A',
      isStarred: false,
      tags: [],
      solutionMetadata: {
        kind: 'USACO',
        usacoId: id,
      },
    });
    report.write(
      `id ${id}: ${problems[id].title.name} (#${problems[id].title.place} from ${problems[id].source.sourceString})\n`
    );
  }
  if (!div_to_probs[problems[id].source.division].find(x => x[0] == id)) {
    div_to_probs[problems[id].source.division].push([
      id,
      `${problems[id].source.year} ${problems[id].source.contest}`,
      problems[id].title.name,
    ]);
  }
  const mon =
    problems[id].source.contest === 'US Open'
      ? 'open'
      : problems[id].source.contest.substring(0, 3).toLowerCase();
  if (!Object.keys(id_to_sol).find(x => x == id)) {
    id_to_sol[id] = `sol_prob${problems[id].title.place}_${problems[
      id
    ].source.division.toLowerCase()}_${mon}${problems[id].source.year
      .toString()
      .substring(2)}.html`;
  }
}
report.write('```\n');
(async () => {
  writeFileSync(
    EXTRAPROBLEMS_PATH,
    await prettier.format(JSON.stringify(extraProblems, null, 2), {
      parser: 'json',
      trailingComma: 'es5',
    })
  );
  writeFileSync(
    DIVTOPROBS_PATH,
    await prettier.format(JSON.stringify(div_to_probs, null, 2), {
      parser: 'json',
      trailingComma: 'es5',
    })
  );
  writeFileSync(
    IDTOSOL_PATH,
    await prettier.format(JSON.stringify(id_to_sol, null, 2), {
      parser: 'json',
      trailingComma: 'es5',
    })
  );
})();
