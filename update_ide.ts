import algoliasearch from 'algoliasearch';
const client = algoliasearch('3CFULMFIDW', process.env.ALGOLIA_API_KEY ?? '');
const index = client.initIndex('usacoProblems');
index.replaceAllObjects(require('./problems.json'));