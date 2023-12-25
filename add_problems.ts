import { createWriteStream, mkdirSync, readFileSync, writeFileSync } from "fs";
import { ProblemData } from "./ProblemData";
import * as prettier from "prettier";

process.chdir(__dirname);
const ids = readFileSync(process.argv[2]).toString().split("\n");
const json_path = process.argv[3];
const extraProblems = require('./' + json_path);
const problems = require('./problems.json') as { [key: string]: ProblemData };
mkdirSync('out');
const report = createWriteStream('out/report.txt');
report.write('added problems:\n```\n');
for (const id in problems) {
  if (!ids.find(x => x == `usaco-${id}`)) {
    extraProblems.EXTRA_PROBLEMS.push({
      uniqueId: `usaco-${id}`,
      name: problems[id].title.name,
      url: problems[id].url,
      source: problems[id].source.division,
      difficulty: "N/A",
      isStarred: false,
      tags: [],
      solutionMetadata: {
        kind: "USACO",
        usacoId: id
      }
    });
    report.write(`id ${id}: ${problems[id].title.name} (#${problems[id].title.place} from ${problems[id].source.sourceString})\n`);
  }
}
report.write('```\n');
(async () => {
  writeFileSync(
    json_path, 
    await prettier.format(JSON.stringify(extraProblems, null, 2), { parser: "json" })
  )
})();