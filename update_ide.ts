import algoliasearch from 'algoliasearch';
import { ProblemData } from './ProblemData';
const client = algoliasearch('3CFULMFIDW', process.argv[2]);
const index = client.initIndex('usacoProblems');
index.replaceAllObjects(
  Object.values(require('./problems.json') as {[key: string]: ProblemData}).map(x => ({
    ...x,
    title: x.title.titleString,
    source: x.source.sourceString
  })),
  { autoGenerateObjectIDIfNotExist: true }
).catch(console.error);